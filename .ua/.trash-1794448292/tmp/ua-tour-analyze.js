const fs = require('fs');
const path = require('path');

const inputPath = process.argv[2] || path.join(__dirname, 'ua-tour-input.json');
const outputPath = process.argv[3] || path.join(__dirname, 'ua-tour-results.json');

const raw = fs.readFileSync(inputPath, 'utf8');
const data = JSON.parse(raw);

const nodes = Array.isArray(data.nodes) ? data.nodes : [];
const edges = Array.isArray(data.edges) ? data.edges : [];
const layers = Array.isArray(data.layers) ? data.layers : [];

const nodeMap = new Map();
const nodeSummaryIndex = {};

for (const n of nodes) {
  nodeMap.set(n.id, n);
  nodeSummaryIndex[n.id] = {
    name: n.name,
    type: n.type,
    filePath: n.filePath || null,
    summary: n.summary || ''
  };
}

// Compute in-degree and out-degree
const inDegree = new Map();
const outDegree = new Map();
const outEdges = new Map();
const inEdges = new Map();

for (const n of nodes) {
  inDegree.set(n.id, 0);
  outDegree.set(n.id, 0);
  outEdges.set(n.id, []);
  inEdges.set(n.id, []);
}

for (const e of edges) {
  if (!nodeMap.has(e.source) || !nodeMap.has(e.target)) continue;
  outDegree.set(e.source, (outDegree.get(e.source) || 0) + 1);
  inDegree.set(e.target, (inDegree.get(e.target) || 0) + 1);
  outEdges.get(e.source).push(e);
  inEdges.get(e.target).push(e);
}

const fanInRanking = nodes
  .map((n) => ({
    id: n.id,
    name: n.name,
    type: n.type,
    filePath: n.filePath,
    inDegree: inDegree.get(n.id) || 0,
    outDegree: outDegree.get(n.id) || 0,
    summary: n.summary
  }))
  .sort((a, b) => b.inDegree - a.inDegree || b.outDegree - a.outDegree)
  .slice(0, 20);

const fanOutRanking = nodes
  .map((n) => ({
    id: n.id,
    name: n.name,
    type: n.type,
    filePath: n.filePath,
    outDegree: outDegree.get(n.id) || 0,
    inDegree: inDegree.get(n.id) || 0,
    summary: n.summary
  }))
  .sort((a, b) => b.outDegree - a.outDegree || b.inDegree - a.inDegree)
  .slice(0, 20);

// Entry point candidates using README/root/entry-point scoring
function scoreEntryPoint(n) {
  const fp = (n.filePath || n.id || '').toLowerCase();
  const name = (n.name || '').toLowerCase();
  const isCode = /\.(py|sh|js|ts)$/.test(fp) || fp === 'setup';
  let score = 0;

  if (n.id === 'document:README.md' || name === 'readme.md') score += 100;
  if (/(^|\/)(__main__|main|app|daemon|nas_agent|svc|init|install|setup)(\.py|\.sh)?$/.test(fp)) score += 60;
  if (!fp.includes('/')) score += 20; // root-level file
  if (fp.startsWith('agent/nas_agent.py') || fp.startsWith('agent/daemon.py')) score += 35;
  if (fp.startsWith('svc_py/__main__.py') || fp.startsWith('docker/cli/svc.sh')) score += 35;
  if (fp.startsWith('shell/init.sh') || fp === 'install.sh') score += 30;
  if (fp.includes('test')) score -= 50;

  const outD = outDegree.get(n.id) || 0;
  const inD = inDegree.get(n.id) || 0;
  score += Math.min(outD * 2, 30);
  score += Math.min(inD, 15);

  return { score, isCode };
}

const scoredCandidates = nodes
  .map((n) => {
    const { score, isCode } = scoreEntryPoint(n);
    return {
      id: n.id,
      name: n.name,
      type: n.type,
      filePath: n.filePath,
      score,
      isCode,
      inDegree: inDegree.get(n.id) || 0,
      outDegree: outDegree.get(n.id) || 0,
      summary: n.summary
    };
  })
  .sort((a, b) => b.score - a.score);

const entryPointCandidates = scoredCandidates.slice(0, 5);

// Top code entry point for BFS traversal
const topCodeEntry = scoredCandidates.find((c) => c.isCode && c.outDegree > 0) || scoredCandidates.find((c) => c.isCode) || scoredCandidates[0];

const bfsVisited = new Set();
const bfsOrder = [];
if (topCodeEntry) {
  const queue = [{ id: topCodeEntry.id, depth: 0, via: null, from: null }];
  bfsVisited.add(topCodeEntry.id);

  while (queue.length > 0) {
    const current = queue.shift();
    const node = nodeMap.get(current.id);
    bfsOrder.push({
      id: current.id,
      name: node ? node.name : current.id,
      filePath: node ? node.filePath : null,
      depth: current.depth,
      via: current.via,
      from: current.from
    });

    const outgoing = outEdges.get(current.id) || [];
    for (const e of outgoing) {
      if ((e.type === 'imports' || e.type === 'calls') && !bfsVisited.has(e.target)) {
        bfsVisited.add(e.target);
        queue.push({
          id: e.target,
          depth: current.depth + 1,
          via: e.type,
          from: current.id
        });
      }
    }
  }
}

const bfsTraversal = {
  startNodeId: topCodeEntry ? topCodeEntry.id : null,
  visitedCount: bfsOrder.length,
  order: bfsOrder
};

// Categorize non-code files: documentation, infrastructure, data, config
const nonCodeFiles = {
  documentation: [],
  infrastructure: [],
  data: [],
  config: []
};

const codeExtRe = /\.(py|sh|js|ts|jsx|tsx)$/;
for (const n of nodes) {
  const fp = (n.filePath || n.id || '').toLowerCase();
  const isCodeFile = n.type === 'file' && (codeExtRe.test(fp) || fp === 'setup');
  if (isCodeFile) continue;

  const entry = {
    id: n.id,
    name: n.name,
    type: n.type,
    filePath: n.filePath,
    inDegree: inDegree.get(n.id) || 0,
    outDegree: outDegree.get(n.id) || 0,
    summary: n.summary
  };

  if (n.type === 'document' || fp.endsWith('.md') || fp.endsWith('.txt')) {
    nonCodeFiles.documentation.push(entry);
  } else if (
    n.type === 'service' ||
    fp.includes('dockerfile') ||
    fp.includes('compose.yml') ||
    fp.includes('compose.yaml') ||
    fp.endsWith('.service') ||
    fp.includes('systemd')
  ) {
    nonCodeFiles.infrastructure.push(entry);
  } else if (fp.endsWith('.json') && !fp.includes('package.json') && !fp.includes('tsconfig')) {
    nonCodeFiles.data.push(entry);
  } else {
    nonCodeFiles.config.push(entry);
  }
}

// Tightly coupled clusters of 2-5 nodes
// Build undirected weighted adjacency among nodes, focusing on strong structural edges
const adj = new Map();
for (const n of nodes) adj.set(n.id, new Map());

for (const e of edges) {
  if (!nodeMap.has(e.source) || !nodeMap.has(e.target) || e.source === e.target) continue;
  const w = typeof e.weight === 'number' ? e.weight : 0.5;
  const bonus = (e.type === 'imports' || e.type === 'calls' || e.type === 'deploys' || e.type === 'configures') ? 0.3 : 0;
  const score = w + bonus;
  adj.get(e.source).set(e.target, (adj.get(e.source).get(e.target) || 0) + score);
  adj.get(e.target).set(e.source, (adj.get(e.target).get(e.source) || 0) + score);
}

// Find mutual / high-density triangles and small cliques/hubs of size 2-5
const usedInCluster = new Set();
const clusters = [];

// Sort nodes by total weighted degree descending (excluding ultra-hubs with >25 neighbors for cluster seeds)
const seedCandidates = nodes
  .map((n) => {
    const neighbors = adj.get(n.id);
    let totalW = 0;
    for (const v of neighbors.values()) totalW += v;
    return { id: n.id, degree: neighbors.size, totalW };
  })
  .filter((x) => x.degree >= 1 && x.degree <= 20)
  .sort((a, b) => b.totalW - a.totalW);

for (const seed of seedCandidates) {
  if (usedInCluster.has(seed.id)) continue;
  const neighbors = [...adj.get(seed.id).entries()]
    .filter(([nid]) => !usedInCluster.has(nid))
    .sort((a, b) => b[1] - a[1]);

  if (neighbors.length === 0) continue;

  const group = [seed.id];
  for (const [nid] of neighbors) {
    if (group.length >= 5) break;
    // Check connectivity to existing group members
    let links = 0;
    for (const gid of group) {
      if (adj.get(nid).has(gid)) links++;
    }
    if (links >= 1 && (group.length < 2 || links >= Math.min(2, group.length))) {
      group.push(nid);
    }
  }

  if (group.length >= 2 && group.length <= 5) {
    // Compute internal edge count
    let internalEdges = 0;
    const groupSet = new Set(group);
    for (const e of edges) {
      if (groupSet.has(e.source) && groupSet.has(e.target)) internalEdges++;
    }
    if (internalEdges >= group.length - 1) {
      for (const gid of group) usedInCluster.add(gid);
      clusters.push({
        size: group.length,
        internalEdges,
        nodes: group.map((id) => {
          const n = nodeMap.get(id);
          return { id, name: n.name, type: n.type, filePath: n.filePath };
        })
      });
    }
  }
  if (clusters.length >= 15) break;
}

const results = {
  meta: {
    totalNodes: nodes.length,
    totalEdges: edges.length,
    generatedAt: new Date().toISOString()
  },
  fanInRanking,
  fanOutRanking,
  entryPointCandidates,
  bfsTraversal,
  nonCodeFiles: {
    counts: {
      documentation: nonCodeFiles.documentation.length,
      infrastructure: nonCodeFiles.infrastructure.length,
      data: nonCodeFiles.data.length,
      config: nonCodeFiles.config.length
    },
    documentation: nonCodeFiles.documentation.slice(0, 30),
    infrastructure: nonCodeFiles.infrastructure.slice(0, 30),
    data: nonCodeFiles.data.slice(0, 30),
    config: nonCodeFiles.config.slice(0, 30)
  },
  clusters,
  layers: {
    count: layers.length,
    list: layers
  },
  nodeSummaryIndex
};

fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf8');
console.log(`Analysis complete: ${nodes.length} nodes, ${edges.length} edges, ${clusters.length} clusters -> ${outputPath}`);
