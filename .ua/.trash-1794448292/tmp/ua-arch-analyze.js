const fs = require('fs');
const path = require('path');

const inputPath = process.argv[2] || path.join(__dirname, 'ua-arch-input.json');
const outputPath = process.argv[3] || path.join(__dirname, 'ua-arch-results.json');

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const fileNodes = data.fileNodes || [];
const importEdges = data.importEdges || [];
const allEdges = data.allEdges || [];

const nodeMap = new Map();
for (const n of fileNodes) {
  nodeMap.set(n.id, n);
}

function getFilePath(node) {
  if (node.filePath) return node.filePath.replace(/\\/g, '/');
  const idx = node.id.indexOf(':');
  return idx >= 0 ? node.id.slice(idx + 1).replace(/\\/g, '/') : node.name || node.id;
}

function getTopGroup(node) {
  const fp = getFilePath(node);
  const parts = fp.split('/').filter(Boolean);
  if (parts.length <= 1) return 'root';
  return parts[0];
}

function getSubGroup(node) {
  const fp = getFilePath(node);
  const parts = fp.split('/').filter(Boolean);
  if (parts.length <= 1) return 'root';
  if (parts.length === 2) return parts[0];
  return `${parts[0]}/${parts[1]}`;
}

// 1. directoryGroups
const directoryGroups = {};
const subDirectoryGroups = {};
for (const n of fileNodes) {
  const top = getTopGroup(n);
  const sub = getSubGroup(n);
  if (!directoryGroups[top]) {
    directoryGroups[top] = { count: 0, types: {}, nodes: [] };
  }
  directoryGroups[top].count++;
  directoryGroups[top].types[n.type] = (directoryGroups[top].types[n.type] || 0) + 1;
  directoryGroups[top].nodes.push({
    id: n.id,
    type: n.type,
    name: n.name,
    filePath: getFilePath(n),
    summary: n.summary || '',
    tags: n.tags || []
  });

  if (!subDirectoryGroups[sub]) {
    subDirectoryGroups[sub] = { count: 0, types: {}, nodeIds: [] };
  }
  subDirectoryGroups[sub].count++;
  subDirectoryGroups[sub].types[n.type] = (subDirectoryGroups[sub].types[n.type] || 0) + 1;
  subDirectoryGroups[sub].nodeIds.push(n.id);
}

// 2. nodeTypeGroups
const nodeTypeGroups = {};
for (const n of fileNodes) {
  if (!nodeTypeGroups[n.type]) {
    nodeTypeGroups[n.type] = { count: 0, nodeIds: [] };
  }
  nodeTypeGroups[n.type].count++;
  nodeTypeGroups[n.type].nodeIds.push(n.id);
}

// 3. crossCategoryEdges
const crossCategoryMap = new Map();
const unknownEdgeEndpoints = { missingSource: 0, missingTarget: 0 };
for (const e of allEdges) {
  const src = nodeMap.get(e.source);
  const tgt = nodeMap.get(e.target);
  if (!src) unknownEdgeEndpoints.missingSource++;
  if (!tgt) unknownEdgeEndpoints.missingTarget++;
  const fromType = src ? src.type : (e.source.split(':')[0] || 'unknown');
  const toType = tgt ? tgt.type : (e.target.split(':')[0] || 'unknown');
  const key = `${fromType}|${toType}|${e.type}`;
  crossCategoryMap.set(key, (crossCategoryMap.get(key) || 0) + 1);
}
const crossCategoryEdges = Array.from(crossCategoryMap.entries())
  .map(([key, count]) => {
    const [fromType, toType, edgeType] = key.split('|');
    return { fromType, toType, edgeType, count };
  })
  .sort((a, b) => b.count - a.count);

// 4. interGroupImports & intraGroupDensity
const interGroupImports = {};
const intraGroupCounts = {};
for (const e of importEdges) {
  const src = nodeMap.get(e.source);
  const tgt = nodeMap.get(e.target);
  if (!src || !tgt) continue;
  const g1 = getTopGroup(src);
  const g2 = getTopGroup(tgt);
  if (g1 === g2) {
    intraGroupCounts[g1] = (intraGroupCounts[g1] || 0) + 1;
  } else {
    const key = `${g1} -> ${g2}`;
    interGroupImports[key] = (interGroupImports[key] || 0) + 1;
  }
}

const intraGroupDensity = {};
for (const [group, info] of Object.entries(directoryGroups)) {
  const n = info.count;
  const intra = intraGroupCounts[group] || 0;
  const possible = n > 1 ? n * (n - 1) : 0;
  intraGroupDensity[group] = {
    nodeCount: n,
    intraImportEdges: intra,
    density: possible > 0 ? Number((intra / possible).toFixed(4)) : 0
  };
}

// Also compute inter-subgroup imports and inter-group allEdges
const interSubGroupImports = {};
for (const e of importEdges) {
  const src = nodeMap.get(e.source);
  const tgt = nodeMap.get(e.target);
  if (!src || !tgt) continue;
  const sg1 = getSubGroup(src);
  const sg2 = getSubGroup(tgt);
  if (sg1 !== sg2) {
    const key = `${sg1} -> ${sg2}`;
    interSubGroupImports[key] = (interSubGroupImports[key] || 0) + 1;
  }
}

const interGroupAllEdges = {};
for (const e of allEdges) {
  const src = nodeMap.get(e.source);
  const tgt = nodeMap.get(e.target);
  if (!src || !tgt) continue;
  const sg1 = getSubGroup(src);
  const sg2 = getSubGroup(tgt);
  if (sg1 !== sg2) {
    const key = `${sg1} -[${e.type}]-> ${sg2}`;
    interGroupAllEdges[key] = (interGroupAllEdges[key] || 0) + 1;
  }
}

// 5. patternMatches & dependencyDirection
const patternChecks = {
  tests: n => getTopGroup(n) === 'tests' || /test_|\.test\.|spec\.|conftest/.test(n.name),
  docsAndSkills: n => n.type === 'document' || getTopGroup(n) === 'docs' || getTopGroup(n) === '.kiro' || getTopGroup(n) === 'docker-nas' || getTopGroup(n) === 'skill-portable',
  agentCore: n => getSubGroup(n).startsWith('agent/core') || getSubGroup(n).startsWith('agent/cache') || getSubGroup(n).startsWith('agent/events') || getSubGroup(n).startsWith('agent/memory') || getSubGroup(n).startsWith('agent/plugins') || getSubGroup(n).startsWith('agent/tools') || getSubGroup(n).startsWith('agent/capabilities') || getSubGroup(n).startsWith('agent/architecture'),
  mcpGateway: n => getSubGroup(n).includes('mcp') || /mcp/i.test(n.name),
  serviceCatalog: n => getSubGroup(n).startsWith('agent/catalog') || n.type === 'service',
  cliTools: n => getTopGroup(n) === 'svc_py' || getSubGroup(n).startsWith('docker/cli'),
  shellAutomation: n => getTopGroup(n) === 'shell' || /^(install\.sh|uninstall\.sh|setup)$/.test(n.name),
  systemdAndDeploy: n => getTopGroup(n) === 'systemd' || /Dockerfile|\.service$|\.timer$/.test(n.name)
};

const patternMatches = {};
for (const [pattern, fn] of Object.entries(patternChecks)) {
  const matched = fileNodes.filter(fn).map(n => n.id);
  patternMatches[pattern] = { count: matched.length, sample: matched.slice(0, 15) };
}

const dependencyDirection = {};
for (const [edgePair, count] of Object.entries(interGroupImports)) {
  const [from, to] = edgePair.split(' -> ');
  const reverse = interGroupImports[`${to} -> ${from}`] || 0;
  dependencyDirection[edgePair] = { forward: count, reverse, net: count - reverse };
}

// 6. deploymentTopology & docCoverage
const deploymentTopology = {
  deploysEdges: [],
  configuresEdges: [],
  triggersEdges: [],
  dependsOnEdges: []
};
const documentedTargets = new Set();
const documentSources = new Set();

for (const e of allEdges) {
  if (e.type === 'deploys') deploymentTopology.deploysEdges.push(e);
  else if (e.type === 'configures') deploymentTopology.configuresEdges.push(e);
  else if (e.type === 'triggers') deploymentTopology.triggersEdges.push(e);
  else if (e.type === 'depends_on') deploymentTopology.dependsOnEdges.push(e);
  else if (e.type === 'documents') {
    documentSources.add(e.source);
    documentedTargets.add(e.target);
  }
}

const docCoverageByGroup = {};
for (const [group, info] of Object.entries(directoryGroups)) {
  const docNodes = info.nodes.filter(n => n.type === 'document').length;
  const targetsCovered = info.nodes.filter(n => documentedTargets.has(n.id)).length;
  docCoverageByGroup[group] = {
    totalNodes: info.count,
    documentNodes: docNodes,
    targetsDocumentedByEdges: targetsCovered
  };
}
const docCoverage = {
  totalDocumentNodes: (nodeTypeGroups.document && nodeTypeGroups.document.count) || 0,
  totalDocumentEdges: allEdges.filter(e => e.type === 'documents').length,
  uniqueTargetsDocumented: documentedTargets.size,
  byGroup: docCoverageByGroup
};

// 7. fileStats
const filesPerGroup = {};
for (const [group, info] of Object.entries(directoryGroups)) {
  filesPerGroup[group] = info.count;
}
const nodeTypeCounts = {};
for (const [t, info] of Object.entries(nodeTypeGroups)) {
  nodeTypeCounts[t] = info.count;
}
const fileStats = {
  totalFileNodes: fileNodes.length,
  totalImportEdges: importEdges.length,
  totalAllEdges: allEdges.length,
  filesPerGroup,
  nodeTypeCounts
};

// 8. fileFanIn & fileFanOut
const importIn = {};
const importOut = {};
const allIn = {};
const allOut = {};

for (const n of fileNodes) {
  importIn[n.id] = 0;
  importOut[n.id] = 0;
  allIn[n.id] = 0;
  allOut[n.id] = 0;
}

for (const e of importEdges) {
  if (importOut[e.source] !== undefined) importOut[e.source]++;
  if (importIn[e.target] !== undefined) importIn[e.target]++;
}
for (const e of allEdges) {
  if (allOut[e.source] !== undefined) allOut[e.source]++;
  if (allIn[e.target] !== undefined) allIn[e.target]++;
}

const topSort = (map, limit = 25) =>
  Object.entries(map)
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([id, count]) => ({ id, count }));

const fileFanIn = {
  importsTop: topSort(importIn),
  allEdgesTop: topSort(allIn)
};
const fileFanOut = {
  importsTop: topSort(importOut),
  allEdgesTop: topSort(allOut)
};

const results = {
  fileStats,
  nodeTypeGroups,
  directoryGroups,
  subDirectoryGroups,
  crossCategoryEdges,
  unknownEdgeEndpoints,
  interGroupImports,
  interSubGroupImports,
  interGroupAllEdges,
  intraGroupDensity,
  patternMatches,
  dependencyDirection,
  deploymentTopology,
  docCoverage,
  fileFanIn,
  fileFanOut
};

fs.writeFileSync(outputPath, JSON.stringify(results, null, 2), 'utf8');
console.log(`Analysis written to ${outputPath}`);
console.log(`Total fileNodes: ${fileNodes.length}`);
console.log('Files per top-level group:', filesPerGroup);
console.log('Node types:', nodeTypeCounts);
