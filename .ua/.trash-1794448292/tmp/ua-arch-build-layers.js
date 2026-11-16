const fs = require('fs');
const path = require('path');

const inputPath = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua/tmp/ua-arch-input.json';
const outputPath = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua/intermediate/layers.json';

const data = JSON.parse(fs.readFileSync(inputPath, 'utf8'));
const fileNodes = data.fileNodes;

const layers = [
  {
    id: 'layer:agente-ia-core',
    name: 'Agente IA, Core y Plugins',
    description: 'Núcleo del agente inteligente basado en Strands Agents (nas_agent.py y daemon.py), lógica de negocio (core), herramientas @tool, sistema de plugins dinámicos, bus de eventos con listener MQTT, caché en memoria, planificador periódico, memoria persistente y contratos arquitectónicos.',
    nodeIds: []
  },
  {
    id: 'layer:gateways-mcp',
    name: 'Gateways MCP Read-Only',
    description: 'Servidores y workers MCP de solo lectura (nas-mcp-gateway y lobehub_mcp) junto con su manifiesto de capacidades, exclusiones de build y Dockerfiles para exposición segura del NAS vía HTTP/stdio/socket.',
    nodeIds: []
  },
  {
    id: 'layer:cli-servicios',
    name: 'CLI de Servicios Docker (Bash y Python)',
    description: 'Interfaz dual de línea de comandos svc para administrar servicios Docker Compose: implementación modular en Bash (docker/cli/) e implementación moderna en Python con Typer, Rich e InquirerPy (svc_py/), conectadas mediante puente de compatibilidad.',
    nodeIds: []
  },
  {
    id: 'layer:catalogo-servicios-docker',
    name: 'Catálogo y Orquestación de Servicios Docker',
    description: 'Catálogo declarativo de servicios del NAS con definiciones Compose (compose.yml), plantillas de variables (.env.example), fichas técnicas (ficha.md), reglas compartidas (_common.yml, _rules.md), indexador catalog.json y automatizaciones auxiliares de servicios.',
    nodeIds: []
  },
  {
    id: 'layer:shell-framework',
    name: 'Shell Framework y Automatización Bash',
    description: 'Framework de terminal Bash cargado por shell/init.sh con librerías de alias, navegación, prompt PS1, autocompletado y diagnóstico, además de scripts operativos del sistema para arranque/apagado escalonado por capas e instalación de Docker.',
    nodeIds: []
  },
  {
    id: 'layer:despliegue-y-systemd',
    name: 'Instalación, Configuración y Servicios Systemd',
    description: 'Puntos de entrada de instalación y desinstalación (setup, install.sh, uninstall.sh, asistente TUI ui/setup.py), manifiestos de dependencias Python, plantillas de configuración de usuario (.config/) y unidades systemd con sus plantillas de entorno.',
    nodeIds: []
  },
  {
    id: 'layer:pruebas-y-calidad',
    name: 'Pruebas Automatizadas y Calidad',
    description: 'Suite de pruebas unitarias con pytest (conftest.py y tests/test_*.py) para validar el agente, herramientas, seguridad, caché, memoria y generación Compose, junto con pruebas de simulación de instalación en Bash.',
    nodeIds: []
  },
  {
    id: 'layer:documentacion',
    name: 'Documentación Técnica y Guías de Servicios',
    description: 'Documentación principal del repositorio (README.md, GUIDE.md, INSTALL.md, AGENTS.md, CONTRIBUTING.md, TODO.md), manuales arquitectónicos, mapas de dependencias e índices de herramientas (docs/) y guías operativas específicas por servicio (docs/services/).',
    nodeIds: []
  },
  {
    id: 'layer:skills-y-gobernanza-ia',
    name: 'Skills Portables, Hooks y Gobernanza Kiro',
    description: 'Ecosistema de conocimiento operativo y automatización para asistentes IA: hooks de ciclo de vida, skills y reglas de steering en .kiro/, paquete de referencia docker-nas/ y distribución portable en skill-portable/.',
    nodeIds: []
  }
];

const byId = Object.fromEntries(layers.map(l => [l.id, l]));

function assignLayer(node) {
  const fp = (node.filePath || '').replace(/\\/g, '/');

  // 1. Gateways MCP
  if (
    fp === 'agent/lobehub_mcp.py' ||
    fp === 'agent/.dockerignore' ||
    fp.startsWith('agent/mcp/')
  ) {
    return 'layer:gateways-mcp';
  }

  // 2. Catálogo de Servicios Docker
  if (fp.startsWith('agent/catalog/')) {
    return 'layer:catalogo-servicios-docker';
  }

  // 3. Agente IA, Core y Plugins
  if (fp.startsWith('agent/')) {
    return 'layer:agente-ia-core';
  }

  // 4. CLI de Servicios Docker (Bash y Python)
  if (fp.startsWith('svc_py/') || fp.startsWith('docker/cli/')) {
    return 'layer:cli-servicios';
  }

  // 5. Shell Framework y Automatización Bash
  if (fp.startsWith('shell/')) {
    return 'layer:shell-framework';
  }

  // 6. Instalación, Configuración y Servicios Systemd
  if (
    fp.startsWith('systemd/') ||
    fp.startsWith('ui/') ||
    fp.startsWith('.config/') ||
    fp === 'setup' ||
    fp === 'install.sh' ||
    fp === 'uninstall.sh' ||
    fp === 'pyproject.toml' ||
    fp === 'requirements.txt'
  ) {
    return 'layer:despliegue-y-systemd';
  }

  // 7. Pruebas Automatizadas y Calidad
  if (fp.startsWith('tests/')) {
    return 'layer:pruebas-y-calidad';
  }

  // 8. Skills Portables, Hooks y Gobernanza Kiro
  if (
    fp.startsWith('.kiro/') ||
    fp.startsWith('docker-nas/') ||
    fp.startsWith('skill-portable/')
  ) {
    return 'layer:skills-y-gobernanza-ia';
  }

  // 9. Documentación Técnica y Guías de Servicios
  if (
    fp.startsWith('docs/') ||
    ['README.md', 'GUIDE.md', 'INSTALL.md', 'CONTRIBUTING.md', 'AGENTS.md', 'TODO.md'].includes(fp)
  ) {
    return 'layer:documentacion';
  }

  throw new Error(`Unassigned node: ${node.id} (filePath=${fp})`);
}

for (const n of fileNodes) {
  const layerId = assignLayer(n);
  byId[layerId].nodeIds.push(n.id);
}

// Programmatic verification
const allAssigned = layers.flatMap(l => l.nodeIds);
const sum = layers.reduce((acc, l) => acc + l.nodeIds.length, 0);
const uniqueAssigned = new Set(allAssigned);
const inputIds = new Set(fileNodes.map(n => n.id));

if (layers.length < 3 || layers.length > 10) {
  throw new Error(`Layer count out of bounds: ${layers.length}`);
}
if (layers.some(l => l.nodeIds.length === 0)) {
  throw new Error('Empty layer detected');
}
if (sum !== fileNodes.length) {
  throw new Error(`Sum mismatch: ${sum} !== ${fileNodes.length}`);
}
if (uniqueAssigned.size !== fileNodes.length) {
  throw new Error(`Duplicate assignments: unique=${uniqueAssigned.size}, expected=${fileNodes.length}`);
}
for (const id of uniqueAssigned) {
  if (!inputIds.has(id)) {
    throw new Error(`Invented node ID: ${id}`);
  }
}

fs.mkdirSync(path.dirname(outputPath), { recursive: true });
fs.writeFileSync(outputPath, JSON.stringify(layers, null, 2), 'utf8');

console.log(`Successfully wrote ${layers.length} layers to ${outputPath}`);
for (const l of layers) {
  console.log(`- ${l.id} (${l.name}): ${l.nodeIds.length} nodes`);
}
console.log(`Verification PASSED: total=${sum}, unique=${uniqueAssigned.size}, input=${fileNodes.length}`);
