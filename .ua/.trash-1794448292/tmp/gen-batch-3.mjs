import fs from 'node:fs';
import path from 'node:path';

const uaDir = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua';
const batches = JSON.parse(fs.readFileSync(path.join(uaDir, 'intermediate', 'batches.json'), 'utf8'));
const batch = Array.isArray(batches) ? batches.find(b => b.batchIndex === 3) : (batches.batches ? batches.batches.find(b => b.batchIndex === 3) : batches['3']);
const extract = JSON.parse(fs.readFileSync(path.join(uaDir, 'tmp', 'ua-file-extract-results-3.json'), 'utf8'));

const nodes = [
  // 1. agent/core/_result.py
  {
    id: 'file:agent/core/_result.py',
    type: 'file',
    name: '_result.py',
    filePath: 'agent/core/_result.py',
    summary: 'Define la estructura estándar de respuesta ToolResult, el enumerado Status y el context manager Timer para todas las herramientas del agente.',
    tags: ['resultado-estructurado', 'dataclass', 'context-manager', 'core'],
    complexity: 'moderate',
    languageNotes: 'Utiliza @dataclass con métodos de fábrica (@classmethod) y __str__ para mantener compatibilidad retroactiva con Strands SDK.'
  },
  {
    id: 'class:agent/core/_result.py:Status',
    type: 'class',
    name: 'Status',
    filePath: 'agent/core/_result.py',
    lineRange: [19, 23],
    summary: 'Enumerado de cadenas que representa los estados semánticos posibles de una herramienta: ok, warning y error.',
    tags: ['enum', 'estado', 'resultado-estructurado'],
    complexity: 'simple'
  },
  {
    id: 'class:agent/core/_result.py:ToolResult',
    type: 'class',
    name: 'ToolResult',
    filePath: 'agent/core/_result.py',
    lineRange: [27, 124],
    summary: 'Dataclass que encapsula el resultado de ejecución de una herramienta con éxito, mensaje, datos estructurados, sugerencias y tiempo transcurrido.',
    tags: ['dataclass', 'serializacion', 'resultado-estructurado', 'api-interna'],
    complexity: 'moderate'
  },
  {
    id: 'class:agent/core/_result.py:Timer',
    type: 'class',
    name: 'Timer',
    filePath: 'agent/core/_result.py',
    lineRange: [127, 149],
    summary: 'Context manager basado en time.perf_counter para medir la duración de operaciones en milisegundos.',
    tags: ['context-manager', 'medicion-tiempo', 'utilidad'],
    complexity: 'simple'
  },

  // 2. agent/core/backup_manager.py
  {
    id: 'file:agent/core/backup_manager.py',
    type: 'file',
    name: 'backup_manager.py',
    filePath: 'agent/core/backup_manager.py',
    summary: 'Centraliza las operaciones de creación, restauración y listado de copias de seguridad de servicios Docker en el NAS.',
    tags: ['gestion-backups', 'docker', 'core', 'servicio'],
    complexity: 'moderate'
  },
  {
    id: 'class:agent/core/backup_manager.py:BackupManager',
    type: 'class',
    name: 'BackupManager',
    filePath: 'agent/core/backup_manager.py',
    lineRange: [24, 179],
    summary: 'Clase con métodos estáticos para crear backups vía CLI svc, listar archivos tar.gz existentes y restaurar con confirmación explícita.',
    tags: ['gestion-backups', 'validacion-seguridad', 'docker'],
    complexity: 'moderate'
  },

  // 3. agent/core/compose_manager.py
  {
    id: 'file:agent/core/compose_manager.py',
    type: 'file',
    name: 'compose_manager.py',
    filePath: 'agent/core/compose_manager.py',
    summary: 'Gestiona la carga de reglas del catálogo, extracción de anchors YAML base, sanitización de valores y validación de archivos Docker Compose.',
    tags: ['docker-compose', 'validacion-yaml', 'seguridad', 'core'],
    complexity: 'complex',
    languageNotes: 'Combina validación estática con PyYAML y verificación en tiempo de ejecución mediante docker compose config --quiet.'
  },
  {
    id: 'class:agent/core/compose_manager.py:ComposeManager',
    type: 'class',
    name: 'ComposeManager',
    filePath: 'agent/core/compose_manager.py',
    lineRange: [39, 287],
    summary: 'Provee métodos estáticos para leer y validar compose.yml contra _rules.md y _compose_base.md, además de sanitizar entradas YAML.',
    tags: ['docker-compose', 'validacion-yaml', 'sanitizacion'],
    complexity: 'complex'
  },

  // 4. agent/core/memory.py
  {
    id: 'file:agent/core/memory.py',
    type: 'file',
    name: 'memory.py',
    filePath: 'agent/core/memory.py',
    summary: 'Implementa la gestión CRUD y curación de la memoria persistente del agente basada en archivos Markdown (MEMORY.md, USER.md, SKILLS.md y sessions/).',
    tags: ['memoria-persistente', 'markdown', 'core', 'curacion'],
    complexity: 'complex',
    languageNotes: 'Clase sin estado con métodos estáticos que retornan ToolResult y aplican límites de tamaño por archivo.'
  },
  {
    id: 'class:agent/core/memory.py:MemoryManager',
    type: 'class',
    name: 'MemoryManager',
    filePath: 'agent/core/memory.py',
    lineRange: [45, 468],
    summary: 'Administra inicialización, lectura, búsqueda por relevancia (recall), registro de hechos/skills/sesiones y poda automática de memoria antigua.',
    tags: ['memoria-persistente', 'busqueda-relevancia', 'curacion'],
    complexity: 'complex'
  },

  // 5. agent/core/service_manager.py
  {
    id: 'file:agent/core/service_manager.py',
    type: 'file',
    name: 'service_manager.py',
    filePath: 'agent/core/service_manager.py',
    summary: 'Centraliza las operaciones de ciclo de vida de servicios Docker Compose: inicio, detención confirmada, reinicio, actualización y consulta de logs.',
    tags: ['ciclo-vida', 'docker-compose', 'core', 'servicio'],
    complexity: 'moderate'
  },
  {
    id: 'class:agent/core/service_manager.py:ServiceManager',
    type: 'class',
    name: 'ServiceManager',
    filePath: 'agent/core/service_manager.py',
    lineRange: [19, 183],
    summary: 'Orquesta comandos docker compose seguros mediante safe_run, guardias read-only y medición de tiempos con Timer.',
    tags: ['ciclo-vida', 'docker-compose', 'control-acceso'],
    complexity: 'moderate'
  },

  // 6. agent/tools/_shell.py
  {
    id: 'file:agent/tools/_shell.py',
    type: 'file',
    name: '_shell.py',
    filePath: 'agent/tools/_shell.py',
    summary: 'Módulo común de ejecución segura de subprocesos con shell=False, validación anti path-traversal de nombres de servicio y modos read-only y dry-run.',
    tags: ['seguridad', 'subprocesos', 'validacion', 'utilidad'],
    complexity: 'complex',
    languageNotes: 'Centraliza la ejecución de comandos externos con subprocess.run(..., shell=False) y resolución segura de rutas con Path.relative_to.'
  },
  {
    id: 'class:agent/tools/_shell.py:InvalidServiceName',
    type: 'class',
    name: 'InvalidServiceName',
    filePath: 'agent/tools/_shell.py',
    lineRange: [42, 44],
    summary: 'Excepción derivada de ValueError lanzada cuando un nombre de servicio o valor es inválido o potencialmente peligroso.',
    tags: ['excepcion', 'validacion', 'seguridad'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:validate_service_name',
    type: 'function',
    name: 'validate_service_name',
    filePath: 'agent/tools/_shell.py',
    lineRange: [47, 93],
    summary: 'Valida nombres de servicio con regex estricta y bloquea path traversal, barras y nombres reservados del sistema.',
    tags: ['validacion', 'seguridad', 'anti-traversal'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/_shell.py:validated_service_path',
    type: 'function',
    name: 'validated_service_path',
    filePath: 'agent/tools/_shell.py',
    lineRange: [96, 121],
    summary: 'Valida el nombre del servicio y verifica que la ruta resuelta permanezca confinada dentro de DOCKER_BASE.',
    tags: ['validacion', 'seguridad', 'rutas'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:safe_run',
    type: 'function',
    name: 'safe_run',
    filePath: 'agent/tools/_shell.py',
    lineRange: [129, 179],
    summary: 'Ejecuta comandos del sistema con shell=False, timeout configurable e intercepción automática en modo dry-run.',
    tags: ['subprocesos', 'seguridad', 'dry-run'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/_shell.py:find_compose',
    type: 'function',
    name: 'find_compose',
    filePath: 'agent/tools/_shell.py',
    lineRange: [187, 208],
    summary: 'Localiza el archivo compose.yml o docker-compose.yml dentro del directorio validado de un servicio.',
    tags: ['docker-compose', 'busqueda-archivos', 'utilidad'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:service_exists_or_error',
    type: 'function',
    name: 'service_exists_or_error',
    filePath: 'agent/tools/_shell.py',
    lineRange: [211, 240],
    summary: 'Comprueba la existencia y validez de un servicio Docker y retorna un mensaje de error con los servicios disponibles si falla.',
    tags: ['validacion', 'docker-compose', 'control-errores'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:is_readonly',
    type: 'function',
    name: 'is_readonly',
    filePath: 'agent/tools/_shell.py',
    lineRange: [257, 262],
    summary: 'Indica si el agente opera en modo solo lectura según la variable de entorno NAS_AGENT_READONLY.',
    tags: ['read-only', 'configuracion', 'seguridad'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:is_dryrun',
    type: 'function',
    name: 'is_dryrun',
    filePath: 'agent/tools/_shell.py',
    lineRange: [265, 271],
    summary: 'Indica si el agente opera en modo simulación dry-run según la variable de entorno NAS_AGENT_DRYRUN.',
    tags: ['dry-run', 'configuracion', 'seguridad'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/_shell.py:readonly_guard',
    type: 'function',
    name: 'readonly_guard',
    filePath: 'agent/tools/_shell.py',
    lineRange: [274, 291],
    summary: 'Bloquea herramientas marcadas como destructivas cuando el modo read-only está activo.',
    tags: ['read-only', 'seguridad', 'guardia'],
    complexity: 'simple'
  },

  // 7. agent/tools/compose_tools.py
  {
    id: 'file:agent/tools/compose_tools.py',
    type: 'file',
    name: 'compose_tools.py',
    filePath: 'agent/tools/compose_tools.py',
    summary: 'Expone herramientas de Strands para leer, validar y crear nuevos servicios Docker Compose con sus archivos .env y README.md.',
    tags: ['herramienta-agente', 'docker-compose', 'creacion-servicios'],
    complexity: 'complex',
    languageNotes: 'Utiliza el decorador @tool de Strands SDK y carga perezosa (lazy import) de ComposeManager para evitar dependencias circulares.'
  },
  {
    id: 'function:agent/tools/compose_tools.py:read_compose',
    type: 'function',
    name: 'read_compose',
    filePath: 'agent/tools/compose_tools.py',
    lineRange: [32, 41],
    summary: 'Tool del agente que delega en ComposeManager.read para devolver el contenido completo del archivo compose de un servicio.',
    tags: ['herramienta-agente', 'docker-compose', 'lectura'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/compose_tools.py:validate_compose',
    type: 'function',
    name: 'validate_compose',
    filePath: 'agent/tools/compose_tools.py',
    lineRange: [45, 55],
    summary: 'Tool del agente que delega en ComposeManager.validate para verificar un compose frente a las reglas del NAS.',
    tags: ['herramienta-agente', 'docker-compose', 'validacion'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/compose_tools.py:create_service',
    type: 'function',
    name: 'create_service',
    filePath: 'agent/tools/compose_tools.py',
    lineRange: [59, 316],
    summary: 'Crea el directorio de un nuevo servicio en /docker/ y genera compose.yml con anchors base, .env y README.md tras validar puertos e inputs.',
    tags: ['herramienta-agente', 'docker-compose', 'generacion-codigo', 'seguridad'],
    complexity: 'complex'
  },

  // 8. agent/tools/diagnostic_tools.py
  {
    id: 'file:agent/tools/diagnostic_tools.py',
    type: 'file',
    name: 'diagnostic_tools.py',
    filePath: 'agent/tools/diagnostic_tools.py',
    summary: 'Provee herramientas de diagnóstico del agente para evaluar la salud de contenedores, detectar conflictos de puertos y depurar servicios.',
    tags: ['herramienta-agente', 'diagnostico', 'monitoreo', 'docker'],
    complexity: 'complex'
  },
  {
    id: 'function:agent/tools/diagnostic_tools.py:service_health',
    type: 'function',
    name: 'service_health',
    filePath: 'agent/tools/diagnostic_tools.py',
    lineRange: [25, 77],
    summary: 'Genera un dashboard de salud de todos los contenedores Docker usando el CLI svc o docker ps como respaldo.',
    tags: ['herramienta-agente', 'healthcheck', 'monitoreo'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/diagnostic_tools.py:port_conflicts',
    type: 'function',
    name: 'port_conflicts',
    filePath: 'agent/tools/diagnostic_tools.py',
    lineRange: [82, 138],
    summary: 'Escanea los archivos compose en /docker/ para construir un mapa de puertos asignados y detectar colisiones entre servicios.',
    tags: ['herramienta-agente', 'puertos', 'diagnostico'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/diagnostic_tools.py:troubleshoot',
    type: 'function',
    name: 'troubleshoot',
    filePath: 'agent/tools/diagnostic_tools.py',
    lineRange: [143, 241],
    summary: 'Ejecuta un diagnóstico integral de un servicio inspeccionando estado, healthcheck, restarts, estadísticas de recursos y errores en logs.',
    tags: ['herramienta-agente', 'diagnostico', 'logs', 'troubleshooting'],
    complexity: 'moderate'
  },

  // 9. agent/tools/discovery_tools.py
  {
    id: 'file:agent/tools/discovery_tools.py',
    type: 'file',
    name: 'discovery_tools.py',
    filePath: 'agent/tools/discovery_tools.py',
    summary: 'Herramientas de descubrimiento y catalogación que detectan servicios en /docker/, analizan sus compose y exportan fichas portables al catálogo.',
    tags: ['herramienta-agente', 'descubrimiento', 'catalogo', 'docker'],
    complexity: 'complex',
    languageNotes: 'Incluye sanitización de secretos en .env y adaptación de rutas relativas de extends al exportar al catálogo.'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:_catalogize_compose_paths',
    type: 'function',
    name: '_catalogize_compose_paths',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [26, 38],
    summary: 'Adapta la referencia relativa ../_common.yml a ../../_common.yml al copiar un compose hacia agent/catalog/services/.',
    tags: ['catalogo', 'docker-compose', 'utilidad'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:list_services',
    type: 'function',
    name: 'list_services',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [43, 96],
    summary: 'Lista todos los servicios Docker con archivo compose en /docker/ indicando cuáles están activos o detenidos.',
    tags: ['herramienta-agente', 'descubrimiento', 'docker'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:scan_compose',
    type: 'function',
    name: 'scan_compose',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [100, 192],
    summary: 'Lee e inspecciona el compose de un servicio extrayendo imagen, puertos, volúmenes, redes, healthcheck y variables redactadas.',
    tags: ['herramienta-agente', 'docker-compose', 'inspeccion'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:auto_catalog',
    type: 'function',
    name: 'auto_catalog',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [196, 523],
    summary: 'Analiza en profundidad un compose (incluyendo stacks multi-servicio) y genera automáticamente su ficha de catálogo en Markdown.',
    tags: ['herramienta-agente', 'catalogo', 'generacion-docs'],
    complexity: 'complex'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:bulk_discover',
    type: 'function',
    name: 'bulk_discover',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [528, 618],
    summary: 'Descubre todos los servicios en /docker/, los exporta al catálogo mediante export_service y regenera el índice catalog.json.',
    tags: ['herramienta-agente', 'descubrimiento', 'catalogo', 'automatizacion'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/discovery_tools.py:export_service',
    type: 'function',
    name: 'export_service',
    filePath: 'agent/tools/discovery_tools.py',
    lineRange: [623, 750],
    summary: 'Exporta compose.yml, .env.example sanitizado, README.md y ficha.md de un servicio desde /docker/ hacia agent/catalog/services/.',
    tags: ['herramienta-agente', 'catalogo', 'sanitizacion', 'exportacion'],
    complexity: 'complex'
  },

  // 10. agent/tools/search_tools.py
  {
    id: 'file:agent/tools/search_tools.py',
    type: 'file',
    name: 'search_tools.py',
    filePath: 'agent/tools/search_tools.py',
    summary: 'Busca información de servicios Docker en el catálogo local o en la API pública de Docker Hub para asistir en la creación de nuevos servicios.',
    tags: ['herramienta-agente', 'busqueda-web', 'docker-hub', 'catalogo'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/search_tools.py:search_service_info',
    type: 'function',
    name: 'search_service_info',
    filePath: 'agent/tools/search_tools.py',
    lineRange: [21, 74],
    summary: 'Verifica primero si el servicio existe en el catálogo local y, en caso contrario, consulta Docker Hub y extrae metadatos del README.',
    tags: ['herramienta-agente', 'busqueda-web', 'catalogo'],
    complexity: 'moderate'
  },
  {
    id: 'function:agent/tools/search_tools.py:_search_dockerhub',
    type: 'function',
    name: '_search_dockerhub',
    filePath: 'agent/tools/search_tools.py',
    lineRange: [77, 106],
    summary: 'Consulta la API de búsqueda de Docker Hub mediante curl vía safe_run y formatea los repositorios principales.',
    tags: ['docker-hub', 'api-externa', 'busqueda-web'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/search_tools.py:_search_github_compose',
    type: 'function',
    name: '_search_github_compose',
    filePath: 'agent/tools/search_tools.py',
    lineRange: [109, 130],
    summary: 'Obtiene la descripción completa de repositorios library o linuxserver en Docker Hub para extraer configuración recomendada.',
    tags: ['docker-hub', 'api-externa', 'metadatos'],
    complexity: 'simple'
  },
  {
    id: 'function:agent/tools/search_tools.py:_extract_info_from_readme',
    type: 'function',
    name: '_extract_info_from_readme',
    filePath: 'agent/tools/search_tools.py',
    lineRange: [133, 155],
    summary: 'Extrae mediante expresiones regulares puertos, variables de entorno y volúmenes comunes desde el texto de un README.',
    tags: ['parsing', 'regex', 'extraccion-metadatos'],
    complexity: 'simple'
  },

  // 11. tests/test_compose_generation.py
  {
    id: 'file:tests/test_compose_generation.py',
    type: 'file',
    name: 'test_compose_generation.py',
    filePath: 'tests/test_compose_generation.py',
    summary: 'Suite de pruebas unitarias para la sanitización YAML, carga de anchors base y lectura de reglas en ComposeManager.',
    tags: ['test', 'test-unitario', 'docker-compose', 'pytest'],
    complexity: 'moderate'
  },
  {
    id: 'class:tests/test_compose_generation.py:TestComposeManagerSanitize',
    type: 'class',
    name: 'TestComposeManagerSanitize',
    filePath: 'tests/test_compose_generation.py',
    lineRange: [8, 39],
    summary: 'Verifica que ComposeManager.sanitize_value acepte imágenes/volúmenes válidos y rechace path traversal, backticks y caracteres de control.',
    tags: ['test', 'sanitizacion', 'seguridad'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_compose_generation.py:TestComposeManagerAnchors',
    type: 'class',
    name: 'TestComposeManagerAnchors',
    filePath: 'tests/test_compose_generation.py',
    lineRange: [42, 57],
    summary: 'Comprueba que los anchors YAML de respaldo y los cargados desde _compose_base.md contengan los bloques obligatorios.',
    tags: ['test', 'docker-compose', 'validacion'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_compose_generation.py:TestComposeManagerRules',
    type: 'class',
    name: 'TestComposeManagerRules',
    filePath: 'tests/test_compose_generation.py',
    lineRange: [60, 69],
    summary: 'Valida que ComposeManager.load_rules devuelva un diccionario con las secciones esperadas cuando existe _rules.md.',
    tags: ['test', 'configuracion', 'validacion'],
    complexity: 'simple'
  },

  // 12. tests/test_memory.py
  {
    id: 'file:tests/test_memory.py',
    type: 'file',
    name: 'test_memory.py',
    filePath: 'tests/test_memory.py',
    summary: 'Suite de pruebas unitarias para MemoryManager que cubre inicialización, registro, recall, skills, modelo de usuario, sesiones y curación.',
    tags: ['test', 'test-unitario', 'memoria-persistente', 'pytest'],
    complexity: 'complex'
  },
  {
    id: 'class:tests/test_memory.py:TestEnsureInitialized',
    type: 'class',
    name: 'TestEnsureInitialized',
    filePath: 'tests/test_memory.py',
    lineRange: [12, 27],
    summary: 'Verifica la creación inicial e idempotencia de MEMORY.md, USER.md, SKILLS.md y el directorio sessions/.',
    tags: ['test', 'inicializacion', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestAddToMemory',
    type: 'class',
    name: 'TestAddToMemory',
    filePath: 'tests/test_memory.py',
    lineRange: [30, 71],
    summary: 'Prueba el agregado de hechos por categoría, validación de longitud, detección de duplicados y actualización de timestamp.',
    tags: ['test', 'validacion', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestRecall',
    type: 'class',
    name: 'TestRecall',
    filePath: 'tests/test_memory.py',
    lineRange: [74, 102],
    summary: 'Valida la búsqueda de contexto en memoria, skills y sesiones, así como el manejo de consultas cortas o sin resultados.',
    tags: ['test', 'busqueda-relevancia', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestAddSkill',
    type: 'class',
    name: 'TestAddSkill',
    filePath: 'tests/test_memory.py',
    lineRange: [105, 128],
    summary: 'Verifica la creación de skills en SKILLS.md, el bloqueo de duplicados y el incremento del contador total.',
    tags: ['test', 'skills', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestUpdateUserModel',
    type: 'class',
    name: 'TestUpdateUserModel',
    filePath: 'tests/test_memory.py',
    lineRange: [131, 146],
    summary: 'Comprueba la inserción de nuevas claves y actualización de preferencias existentes en USER.md.',
    tags: ['test', 'perfil-usuario', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestSaveSession',
    type: 'class',
    name: 'TestSaveSession',
    filePath: 'tests/test_memory.py',
    lineRange: [149, 158],
    summary: 'Verifica el guardado de resúmenes de sesión con nombre slugificado en el subdirectorio sessions/.',
    tags: ['test', 'sesiones', 'memoria-persistente'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestCuration',
    type: 'class',
    name: 'TestCuration',
    filePath: 'tests/test_memory.py',
    lineRange: [161, 190],
    summary: 'Prueba la eliminación de sesiones y entradas de memoria que superan la antigüedad máxima configurada.',
    tags: ['test', 'curacion', 'limpieza-datos'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_memory.py:TestMemoryStats',
    type: 'class',
    name: 'TestMemoryStats',
    filePath: 'tests/test_memory.py',
    lineRange: [193, 210],
    summary: 'Valida la estructura y los cálculos de tamaño y conteo devueltos por MemoryManager.get_memory_stats.',
    tags: ['test', 'metricas', 'memoria-persistente'],
    complexity: 'simple'
  },

  // 13. tests/test_result.py
  {
    id: 'file:tests/test_result.py',
    type: 'file',
    name: 'test_result.py',
    filePath: 'tests/test_result.py',
    summary: 'Pruebas unitarias para ToolResult y Timer, verificando fábricas de estado, serialización a dict, compatibilidad __str__ y medición de tiempo.',
    tags: ['test', 'test-unitario', 'resultado-estructurado', 'pytest'],
    complexity: 'moderate'
  },
  {
    id: 'class:tests/test_result.py:TestToolResult',
    type: 'class',
    name: 'TestToolResult',
    filePath: 'tests/test_result.py',
    lineRange: [8, 67],
    summary: 'Comprueba los métodos ok, warn, error, to_dict, valores por defecto y conversión a cadena de ToolResult.',
    tags: ['test', 'resultado-estructurado', 'serializacion'],
    complexity: 'moderate'
  },
  {
    id: 'class:tests/test_result.py:TestTimer',
    type: 'class',
    name: 'TestTimer',
    filePath: 'tests/test_result.py',
    lineRange: [70, 83],
    summary: 'Valida que Timer mida intervalos con time.sleep y retorne valores cercanos a cero sin esperas.',
    tags: ['test', 'medicion-tiempo', 'context-manager'],
    complexity: 'simple'
  },

  // 14. tests/test_tool_result.py
  {
    id: 'file:tests/test_tool_result.py',
    type: 'file',
    name: 'test_tool_result.py',
    filePath: 'tests/test_tool_result.py',
    summary: 'Suite complementaria de pruebas unitarias para ToolResult y Timer organizada por tipo de resultado y serialización.',
    tags: ['test', 'test-unitario', 'resultado-estructurado', 'pytest'],
    complexity: 'moderate'
  },
  {
    id: 'class:tests/test_tool_result.py:TestToolResultOk',
    type: 'class',
    name: 'TestToolResultOk',
    filePath: 'tests/test_tool_result.py',
    lineRange: [8, 24],
    summary: 'Verifica éxito, estado OK, datos, sugerencias y representación en texto de ToolResult.ok.',
    tags: ['test', 'resultado-estructurado', 'validacion'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_tool_result.py:TestToolResultError',
    type: 'class',
    name: 'TestToolResultError',
    filePath: 'tests/test_tool_result.py',
    lineRange: [27, 35],
    summary: 'Verifica que ToolResult.error marque success=False, estado ERROR y mensaje legible.',
    tags: ['test', 'control-errores', 'resultado-estructurado'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_tool_result.py:TestToolResultWarn',
    type: 'class',
    name: 'TestToolResultWarn',
    filePath: 'tests/test_tool_result.py',
    lineRange: [38, 42],
    summary: 'Comprueba que ToolResult.warn mantenga success=True con estado Status.WARNING.',
    tags: ['test', 'advertencias', 'resultado-estructurado'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_tool_result.py:TestToolResultSerialization',
    type: 'class',
    name: 'TestToolResultSerialization',
    filePath: 'tests/test_tool_result.py',
    lineRange: [45, 58],
    summary: 'Valida la salida de to_dict y __repr__ en instancias de ToolResult.',
    tags: ['test', 'serializacion', 'resultado-estructurado'],
    complexity: 'simple'
  },
  {
    id: 'class:tests/test_tool_result.py:TestTimer',
    type: 'class',
    name: 'TestTimer',
    filePath: 'tests/test_tool_result.py',
    lineRange: [61, 67],
    summary: 'Comprueba que Timer registre correctamente el tiempo transcurrido durante una pausa de 50ms.',
    tags: ['test', 'medicion-tiempo', 'context-manager'],
    complexity: 'simple'
  },

  // 15. tests/test_validation.py
  {
    id: 'file:tests/test_validation.py',
    type: 'file',
    name: 'test_validation.py',
    filePath: 'tests/test_validation.py',
    summary: 'Pruebas unitarias de seguridad para validate_service_name frente a nombres válidos, path traversal e inyección de comandos.',
    tags: ['test', 'seguridad', 'validacion', 'pytest'],
    complexity: 'moderate'
  },
  {
    id: 'class:tests/test_validation.py:TestValidateServiceName',
    type: 'class',
    name: 'TestValidateServiceName',
    filePath: 'tests/test_validation.py',
    lineRange: [16, 68],
    summary: 'Verifica la aceptación de nombres permitidos y el lanzamiento de InvalidServiceName ante traversal, espacios, rutas absolutas y metacaracteres shell.',
    tags: ['test', 'seguridad', 'anti-inyeccion'],
    complexity: 'moderate'
  }
];

const edges = [];
function addEdge(source, target, type, weight) {
  if (source === target) return;
  edges.push({ source, target, type, direction: 'forward', weight });
}

// 1. contains + exports
const exportedSet = new Set();
for (const r of extract.results) {
  for (const e of (r.exports || [])) {
    exportedSet.add(`${r.path}:${e.name}`);
  }
}
for (const n of nodes) {
  if (n.type !== 'file') {
    const fileId = `file:${n.filePath}`;
    addEdge(fileId, n.id, 'contains', 1.0);
    if (exportedSet.has(`${n.filePath}:${n.name}`)) {
      addEdge(fileId, n.id, 'exports', 0.8);
    }
  }
}

// 2. imports (strict 1:1 with batchImportData)
let expectedImports = 0;
for (const [srcFile, targets] of Object.entries(batch.batchImportData)) {
  for (const tgtFile of targets) {
    addEdge(`file:${srcFile}`, `file:${tgtFile}`, 'imports', 0.7);
    expectedImports++;
  }
}

// 3. depends_on (lazy import in compose_tools.py -> compose_manager.py)
addEdge('file:agent/tools/compose_tools.py', 'file:agent/core/compose_manager.py', 'depends_on', 0.6);

// 4. calls
const callPairs = [
  ['class:agent/core/backup_manager.py:BackupManager', 'function:agent/tools/_shell.py:readonly_guard'],
  ['class:agent/core/backup_manager.py:BackupManager', 'function:agent/tools/_shell.py:validated_service_path'],
  ['class:agent/core/backup_manager.py:BackupManager', 'function:agent/tools/_shell.py:validate_service_name'],
  ['class:agent/core/backup_manager.py:BackupManager', 'function:agent/tools/_shell.py:safe_run'],
  ['class:agent/core/backup_manager.py:BackupManager', 'class:agent/core/_result.py:ToolResult'],
  ['class:agent/core/backup_manager.py:BackupManager', 'class:agent/core/_result.py:Timer'],

  ['class:agent/core/compose_manager.py:ComposeManager', 'function:agent/tools/_shell.py:validate_service_name'],
  ['class:agent/core/compose_manager.py:ComposeManager', 'function:agent/tools/_shell.py:validated_service_path'],
  ['class:agent/core/compose_manager.py:ComposeManager', 'function:agent/tools/_shell.py:find_compose'],
  ['class:agent/core/compose_manager.py:ComposeManager', 'function:agent/tools/_shell.py:safe_run'],
  ['class:agent/core/compose_manager.py:ComposeManager', 'class:agent/tools/_shell.py:InvalidServiceName'],
  ['class:agent/core/compose_manager.py:ComposeManager', 'class:agent/core/_result.py:ToolResult'],

  ['class:agent/core/memory.py:MemoryManager', 'class:agent/core/_result.py:ToolResult'],

  ['class:agent/core/service_manager.py:ServiceManager', 'function:agent/tools/_shell.py:service_exists_or_error'],
  ['class:agent/core/service_manager.py:ServiceManager', 'function:agent/tools/_shell.py:find_compose'],
  ['class:agent/core/service_manager.py:ServiceManager', 'function:agent/tools/_shell.py:readonly_guard'],
  ['class:agent/core/service_manager.py:ServiceManager', 'function:agent/tools/_shell.py:safe_run'],
  ['class:agent/core/service_manager.py:ServiceManager', 'class:agent/core/_result.py:ToolResult'],
  ['class:agent/core/service_manager.py:ServiceManager', 'class:agent/core/_result.py:Timer'],

  ['function:agent/tools/_shell.py:validated_service_path', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/_shell.py:find_compose', 'function:agent/tools/_shell.py:validated_service_path'],
  ['function:agent/tools/_shell.py:service_exists_or_error', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/_shell.py:service_exists_or_error', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/_shell.py:safe_run', 'function:agent/tools/_shell.py:is_dryrun'],
  ['function:agent/tools/_shell.py:readonly_guard', 'function:agent/tools/_shell.py:is_readonly'],

  ['function:agent/tools/compose_tools.py:read_compose', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['function:agent/tools/compose_tools.py:validate_compose', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['function:agent/tools/compose_tools.py:create_service', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['function:agent/tools/compose_tools.py:create_service', 'function:agent/tools/_shell.py:readonly_guard'],
  ['function:agent/tools/compose_tools.py:create_service', 'function:agent/tools/_shell.py:validated_service_path'],
  ['function:agent/tools/compose_tools.py:create_service', 'function:agent/tools/_shell.py:safe_run'],
  ['function:agent/tools/compose_tools.py:create_service', 'class:agent/core/_result.py:ToolResult'],

  ['function:agent/tools/diagnostic_tools.py:service_health', 'function:agent/tools/_shell.py:safe_run'],
  ['function:agent/tools/diagnostic_tools.py:port_conflicts', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/diagnostic_tools.py:port_conflicts', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/diagnostic_tools.py:troubleshoot', 'function:agent/tools/_shell.py:service_exists_or_error'],
  ['function:agent/tools/diagnostic_tools.py:troubleshoot', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/diagnostic_tools.py:troubleshoot', 'function:agent/tools/_shell.py:safe_run'],

  ['function:agent/tools/discovery_tools.py:list_services', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/discovery_tools.py:list_services', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/discovery_tools.py:list_services', 'function:agent/tools/_shell.py:safe_run'],
  ['function:agent/tools/discovery_tools.py:scan_compose', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/discovery_tools.py:scan_compose', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/discovery_tools.py:auto_catalog', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/discovery_tools.py:auto_catalog', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/discovery_tools.py:bulk_discover', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/discovery_tools.py:bulk_discover', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/discovery_tools.py:bulk_discover', 'function:agent/tools/discovery_tools.py:export_service'],
  ['function:agent/tools/discovery_tools.py:bulk_discover', 'class:agent/core/_result.py:ToolResult'],
  ['function:agent/tools/discovery_tools.py:bulk_discover', 'class:agent/core/_result.py:Timer'],
  ['function:agent/tools/discovery_tools.py:export_service', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/discovery_tools.py:export_service', 'function:agent/tools/_shell.py:find_compose'],
  ['function:agent/tools/discovery_tools.py:export_service', 'function:agent/tools/discovery_tools.py:_catalogize_compose_paths'],
  ['function:agent/tools/discovery_tools.py:export_service', 'function:agent/tools/discovery_tools.py:auto_catalog'],
  ['function:agent/tools/discovery_tools.py:export_service', 'class:agent/core/_result.py:ToolResult'],

  ['function:agent/tools/search_tools.py:search_service_info', 'function:agent/tools/_shell.py:validate_service_name'],
  ['function:agent/tools/search_tools.py:search_service_info', 'function:agent/tools/search_tools.py:_search_dockerhub'],
  ['function:agent/tools/search_tools.py:search_service_info', 'function:agent/tools/search_tools.py:_search_github_compose'],
  ['function:agent/tools/search_tools.py:_search_dockerhub', 'function:agent/tools/_shell.py:safe_run'],
  ['function:agent/tools/search_tools.py:_search_github_compose', 'function:agent/tools/_shell.py:safe_run'],
  ['function:agent/tools/search_tools.py:_search_github_compose', 'function:agent/tools/search_tools.py:_extract_info_from_readme'],

  ['class:tests/test_compose_generation.py:TestComposeManagerSanitize', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['class:tests/test_compose_generation.py:TestComposeManagerAnchors', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['class:tests/test_compose_generation.py:TestComposeManagerRules', 'class:agent/core/compose_manager.py:ComposeManager'],
  ['class:tests/test_memory.py:TestEnsureInitialized', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestAddToMemory', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestRecall', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestAddSkill', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestUpdateUserModel', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestSaveSession', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestCuration', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_memory.py:TestMemoryStats', 'class:agent/core/memory.py:MemoryManager'],
  ['class:tests/test_result.py:TestToolResult', 'class:agent/core/_result.py:ToolResult'],
  ['class:tests/test_result.py:TestTimer', 'class:agent/core/_result.py:Timer'],
  ['class:tests/test_tool_result.py:TestToolResultOk', 'class:agent/core/_result.py:ToolResult'],
  ['class:tests/test_tool_result.py:TestToolResultError', 'class:agent/core/_result.py:ToolResult'],
  ['class:tests/test_tool_result.py:TestToolResultWarn', 'class:agent/core/_result.py:ToolResult'],
  ['class:tests/test_tool_result.py:TestToolResultSerialization', 'class:agent/core/_result.py:ToolResult'],
  ['class:tests/test_tool_result.py:TestTimer', 'class:agent/core/_result.py:Timer'],
  ['class:tests/test_validation.py:TestValidateServiceName', 'function:agent/tools/_shell.py:validate_service_name']
];
for (const [s, t] of callPairs) {
  addEdge(s, t, 'calls', 0.8);
}

// 5. tested_by (production -> test)
addEdge('file:agent/core/compose_manager.py', 'file:tests/test_compose_generation.py', 'tested_by', 0.5);
addEdge('file:agent/tools/_shell.py', 'file:tests/test_validation.py', 'tested_by', 0.5);
addEdge('file:agent/core/memory.py', 'file:tests/test_memory.py', 'tested_by', 0.5);
addEdge('file:agent/core/_result.py', 'file:tests/test_result.py', 'tested_by', 0.5);
addEdge('file:agent/core/_result.py', 'file:tests/test_tool_result.py', 'tested_by', 0.5);

// Validate
const nodeIds = new Set(nodes.map(n => n.id));
if (nodeIds.size !== nodes.length) throw new Error('Duplicate node IDs');
for (const e of edges) {
  if (!nodeIds.has(e.source) || !nodeIds.has(e.target)) {
    throw new Error(`Dangling edge: ${e.source} -> ${e.target}`);
  }
}
const actualImports = edges.filter(e => e.type === 'imports').length;
if (actualImports !== expectedImports) {
  throw new Error(`Import count mismatch: ${actualImports} vs ${expectedImports}`);
}

const filesSorted = [...new Set(nodes.map(n => n.filePath))].sort();
const parts = Math.ceil(Math.max(nodes.length / 60, edges.length / 120));
const chunkSize = Math.ceil(filesSorted.length / parts);
console.log(`Total nodes: ${nodes.length}, Total edges: ${edges.length} (imports: ${actualImports}), Parts: ${parts}`);

for (let p = 0; p < parts; p++) {
  const partFiles = new Set(filesSorted.slice(p * chunkSize, (p + 1) * chunkSize));
  const partNodes = nodes.filter(n => partFiles.has(n.filePath));
  const partNodeIds = new Set(partNodes.map(n => n.id));
  const partEdges = edges.filter(e => partNodeIds.has(e.source));
  if (partNodes.length > 60 || partEdges.length > 120) {
    throw new Error(`Part ${p + 1} exceeds limits: ${partNodes.length} nodes, ${partEdges.length} edges`);
  }
  const outPath = path.join(uaDir, 'intermediate', `batch-3-part-${p + 1}.json`);
  fs.writeFileSync(outPath, JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2), 'utf8');
  console.log(`Wrote ${outPath}: ${partNodes.length} nodes, ${partEdges.length} edges`);
}
