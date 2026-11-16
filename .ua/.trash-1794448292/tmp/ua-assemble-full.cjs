const fs = require('fs');
const { execSync } = require('child_process');

const root = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles';
const ua = root + '/.ua';

const scan = JSON.parse(fs.readFileSync(ua + '/intermediate/scan-result.json', 'utf8'));
const assembled = JSON.parse(fs.readFileSync(ua + '/intermediate/assembled-graph.json', 'utf8'));
let layers = JSON.parse(fs.readFileSync(ua + '/intermediate/layers.json', 'utf8'));
if (!Array.isArray(layers) && Array.isArray(layers.layers)) layers = layers.layers;

let tour = JSON.parse(fs.readFileSync(ua + '/intermediate/tour.json', 'utf8'));
if (!Array.isArray(tour) && Array.isArray(tour.steps)) tour = tour.steps;

const nodeIds = new Set(assembled.nodes.map(n => n.id));
tour = tour.map(s => {
  const step = {
    order: s.order,
    title: s.title,
    description: s.description || s.whyItMatters,
    nodeIds: (s.nodeIds || s.nodesToInspect || []).filter(id => nodeIds.has(id))
  };
  if (s.languageLesson) step.languageLesson = s.languageLesson;
  return step;
}).sort((a, b) => a.order - b.order);

const gitCommitHash = execSync(`git -C "${root}" rev-parse HEAD`, { encoding: 'utf8' }).trim();
const fullGraph = {
  version: '1.0.0',
  project: {
    name: scan.name,
    languages: scan.languages,
    frameworks: scan.frameworks,
    description: scan.description,
    analyzedAt: new Date().toISOString(),
    gitCommitHash
  },
  nodes: assembled.nodes,
  edges: assembled.edges,
  layers,
  tour
};

fs.writeFileSync(ua + '/intermediate/assembled-graph.json', JSON.stringify(fullGraph, null, 2));
console.log('Assembled full KnowledgeGraph:', fullGraph.nodes.length, 'nodes,', fullGraph.edges.length, 'edges,', fullGraph.layers.length, 'layers,', fullGraph.tour.length, 'tour steps.');
