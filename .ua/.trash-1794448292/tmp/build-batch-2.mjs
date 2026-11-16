import fs from "node:fs";
import path from "node:path";

const uaDir = "C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua";
const outDir = path.join(uaDir, "intermediate");
const rawBatches = JSON.parse(fs.readFileSync(path.join(outDir, "batches.json"), "utf8"));
const batches = Array.isArray(rawBatches) ? rawBatches : (rawBatches.batches || rawBatches);
const batch2 = Array.isArray(batches) ? batches[2] : batches["2"];
const batchImportData = batch2.batchImportData || {};

const nodes = [];
const edges = [];

function addFile(filePath, summary, tags, complexity, languageNotes) {
  nodes.push({
    id: `file:${filePath}`,
    type: "file",
    name: path.posix.basename(filePath),
    filePath,
    language: "python",
    summary,
    tags,
    complexity,
    languageNotes,
  });
}

function addClass(filePath, name, lineRange, summary, tags, complexity, exported = true) {
  const id = `class:${filePath}:${name}`;
  nodes.push({
    id,
    type: "class",
    name,
    filePath,
    language: "python",
    lineRange,
    summary,
    tags,
    complexity,
  });
  edges.push({
    source: `file:${filePath}`,
    target: id,
    type: "contains",
    direction: "forward",
    weight: 1.0,
  });
  if (exported) {
    edges.push({
      source: `file:${filePath}`,
      target: id,
      type: "exports",
      direction: "forward",
      weight: 0.8,
    });
  }
  return id;
}

function addFunc(filePath, name, lineRange, summary, tags, complexity, exported = true) {
  const id = `function:${filePath}:${name}`;
  nodes.push({
    id,
    type: "function",
    name,
    filePath,
    language: "python",
    lineRange,
    summary,
    tags,
    complexity,
  });
  edges.push({
    source: `file:${filePath}`,
    target: id,
    type: "contains",
    direction: "forward",
    weight: 1.0,
  });
  if (exported) {
    edges.push({
      source: `file:${filePath}`,
      target: id,
      type: "exports",
      direction: "forward",
      weight: 0.8,
    });
  }
  return id;
}

function addCall(source, target, description = "") {
  if (source === target) return;
  const e = {
    source,
    target,
    type: "calls",
    direction: "forward",
    weight: 0.8,
  };
  if (description) e.description = description;
  edges.push(e);
}

// ── 1. agent/core/_result.py ─────────────────────────────────────────────
{
  const f = "agent/core/_result.py";
  addFile(
    f,
    "Define el modelo de resultado estructurado ToolResult, el enum Status y el gestor de contexto Timer para todas las herramientas del agente.",
    ["resultado-estructurado", "dataclass", "medicion-tiempo", "compatibilidad-strands"],
    "simple",
    "Módulo Python con dataclasses, Enum tipado y compatibilidad con Strands SDK mediante __str__."
  );
  addClass(
    f, "Status", [19, 23],
    "Enumeración de estados semánticos posibles para la salida de una herramienta (ok, warning, error).",
    ["enum-estado", "semaforo-resultado", "tipado-python"],
    "simple", true
  );
  addClass(
    f, "ToolResult", [27, 124],
    "Dataclass que encapsula éxito, estado, mensaje, datos estructurados, sugerencias y tiempo de ejecución de cada herramienta.",
    ["resultado-tool", "serializacion-dict", "dataclass-python"],
    "moderate", true
  );
  addClass(
    f, "Timer", [127, 149],
    "Gestor de contexto basado en time.perf_counter para medir la duración en milisegundos de operaciones del agente.",
    ["context-manager", "cronometro-ms", "rendimiento"],
    "simple", true
  );
  addFunc(f, "ToolResult.ok", [59, 76], "Constructor de fábrica que crea un ToolResult exitoso con estado OK.", ["factory-method", "estado-ok", "resultado-tool"], "simple", false);
  addFunc(f, "ToolResult.warn", [79, 94], "Constructor de fábrica que crea un ToolResult exitoso con estado WARNING para advertencias o confirmaciones pendientes.", ["factory-method", "estado-warning", "confirmacion"], "simple", false);
  addFunc(f, "ToolResult.error", [97, 112], "Constructor de fábrica que crea un ToolResult fallido con estado ERROR.", ["factory-method", "estado-error", "manejo-errores"], "simple", false);
  addFunc(f, "ToolResult.to_dict", [114, 124], "Serializa los campos del ToolResult a un diccionario estándar para registro y auditoría.", ["serializacion-json", "auditoria", "diccionario"], "simple", false);
}

// ── 2. agent/core/backup_manager.py ──────────────────────────────────────
{
  const f = "agent/core/backup_manager.py";
  addFile(
    f,
    "Centraliza la lógica de creación, restauración y listado de respaldos tar.gz para servicios Docker en /docker/backups.",
    ["backups-docker", "restauracion-servicios", "gestion-archivos", "nucleo-agente"],
    "moderate",
    "Clase estática en Python que delega la ejecución de comandos al binario CLI 'svc' mediante safe_run."
  );
  addClass(
    f, "BackupManager", [24, 179],
    "Gestor sin estado con métodos estáticos para respaldar servicios, restaurar el último archivo tar.gz con confirmación y listar respaldos.",
    ["gestor-backups", "metodos-estaticos", "confirmacion-segura"],
    "moderate", true
  );
  addFunc(f, "BackupManager.backup", [28, 61], "Valida modo read-only y ruta del servicio antes de ejecutar 'svc backup' con cronómetro.", ["crear-backup", "guardia-readonly", "comando-svc"], "moderate", false);
  addFunc(f, "BackupManager.restore", [64, 130], "Lista los últimos 10 respaldos disponibles y exige confirmación explícita antes de ejecutar 'svc restore'.", ["restaurar-backup", "accion-destructiva", "confirmacion-usuario"], "moderate", false);
  addFunc(f, "BackupManager.list_all", [133, 179], "Agrupa los archivos .tar.gz de /docker/backups por servicio y calcula el tamaño total almacenado.", ["listar-backups", "reporte-espacio", "inventario"], "simple", false);
}

// ── 3. agent/core/compose_manager.py ─────────────────────────────────────
{
  const f = "agent/core/compose_manager.py";
  addFile(
    f,
    "Gestiona la lectura, sanitización de valores, carga de reglas/anchors y validación integral de archivos Docker Compose.",
    ["docker-compose", "validacion-yaml", "anchors-base", "seguridad-inputs"],
    "complex",
    "Combina parsing con PyYAML, frontmatter opcional y validación mediante 'docker compose config'."
  );
  addClass(
    f, "ComposeManager", [39, 287],
    "Clase estática encargada de cargar reglas de _rules.md, extraer anchors de _compose_base.md, sanitizar campos y auditar archivos compose.",
    ["gestor-compose", "auditoria-servicios", "reglas-nas"],
    "complex", true
  );
  addFunc(f, "ComposeManager.load_rules", [43, 52], "Carga metadatos de reglas operativas desde el frontmatter de agent/catalog/_rules.md.", ["carga-reglas", "frontmatter", "catalogo-nas"], "simple", false);
  addFunc(f, "ComposeManager.load_compose_base_anchors", [55, 66], "Extrae el bloque YAML de anchors compartidos desde _compose_base.md o recurre al respaldo integrado.", ["anchors-yaml", "plantilla-base", "configuracion-comun"], "simple", false);
  addFunc(f, "ComposeManager._fallback_anchors", [69, 94], "Devuelve los anchors YAML mínimos de seguridad, healthcheck, logging y recursos cuando falta _compose_base.md.", ["anchors-respaldo", "valores-defecto", "resiliencia"], "simple", false);
  addFunc(f, "ComposeManager.sanitize_value", [97, 112], "Rechaza caracteres de control, backticks y secuencias de path traversal antes de interpolar valores en YAML.", ["sanitizacion-yaml", "prevencion-inyeccion", "seguridad"], "simple", false);
  addFunc(f, "ComposeManager.read", [115, 133], "Valida el nombre del servicio y devuelve el contenido textual de su archivo compose.", ["lectura-compose", "inspeccion-servicio", "yaml"], "simple", false);
  addFunc(f, "ComposeManager.validate", [136, 287], "Audita sintaxis YAML, anchors obligatorios, política de reinicio, puertos reservados, credenciales inline y 'docker compose config'.", ["validacion-compose", "puertos-reservados", "deteccion-secretos"], "complex", false);
}

// ── 4. agent/core/memory.py ──────────────────────────────────────────────
{
  const f = "agent/core/memory.py";
  addFile(
    f,
    "Implementa el sistema de memoria persistente basado en archivos Markdown (MEMORY.md, USER.md, SKILLS.md y sessions/).",
    ["memoria-persistente", "archivos-markdown", "busqueda-recall", "curacion-datos"],
    "complex",
    "Permite sobrescribir la ruta mediante la variable de entorno NAS_AGENT_MEMORY_DIR para pruebas aisladas."
  );
  addClass(
    f, "MemoryManager", [45, 468],
    "Gestor sin estado para inicializar, escribir, consultar, podar y medir los archivos Markdown de memoria del agente.",
    ["gestor-memoria", "crud-markdown", "historial-sesiones"],
    "complex", true
  );
  addFunc(f, "MemoryManager.ensure_initialized", [51, 80], "Crea los directorios y archivos iniciales MEMORY.md, USER.md, SKILLS.md y sessions/ si no existen.", ["inicializacion-archivos", "idempotencia", "estructura-memoria"], "simple", false);
  addFunc(f, "MemoryManager.add_to_memory", [99, 163], "Valida categoría, longitud y duplicados antes de insertar un hecho fechado en MEMORY.md.", ["registro-hechos", "control-duplicados", "limite-tamano"], "moderate", false);
  addFunc(f, "MemoryManager.update_user_model", [174, 211], "Actualiza o agrega pares clave-valor de preferencias técnicas dentro de USER.md.", ["perfil-usuario", "preferencias-tecnicas", "actualizacion-markdown"], "moderate", false);
  addFunc(f, "MemoryManager.add_skill", [222, 274], "Registra un procedimiento reutilizable nuevo en SKILLS.md y actualiza el contador global de skills.", ["registro-skills", "procedimientos", "contador-skills"], "moderate", false);
  addFunc(f, "MemoryManager.save_session", [279, 300], "Guarda el resumen de una sesión con slug normalizado por fecha en el subdirectorio sessions/.", ["resumen-sesion", "archivo-diario", "slug-nombre"], "simple", false);
  addFunc(f, "MemoryManager.recall", [305, 377], "Busca por palabras clave priorizando triggers de SKILLS.md, entradas de MEMORY.md y las últimas 20 sesiones.", ["busqueda-memoria", "recuperacion-contexto", "prioridad-skills"], "complex", false);
  addFunc(f, "MemoryManager.trim_sessions", [382, 408], "Elimina archivos de sesión cuya fecha en el nombre supere la antigüedad máxima permitida.", ["curacion-sesiones", "limpieza-antiguos", "retencion"], "simple", false);
  addFunc(f, "MemoryManager.prune_old_entries", [411, 441], "Poda entradas fechadas de MEMORY.md más antiguas que max_age_days conservando las recientes.", ["poda-memoria", "limpieza-entradas", "mantenimiento"], "moderate", false);
  addFunc(f, "MemoryManager.get_memory_stats", [446, 468], "Calcula tamaños en KB, cantidad de skills y número de sesiones almacenadas.", ["metricas-memoria", "estadisticas-uso", "monitoreo"], "simple", false);
}

// ── 5. agent/core/service_manager.py ─────────────────────────────────────
{
  const f = "agent/core/service_manager.py";
  addFile(
    f,
    "Centraliza las operaciones de ciclo de vida de contenedores Docker Compose: iniciar, detener, reiniciar, actualizar y consultar logs.",
    ["ciclo-vida-docker", "compose-cli", "control-servicios", "nucleo-agente"],
    "moderate",
    "Protege operaciones destructivas mediante readonly_guard y confirmación explícita para detener servicios."
  );
  addClass(
    f, "ServiceManager", [19, 183],
    "Gestor estático del ciclo de vida de servicios Docker Compose con soporte de cronómetro y sugerencias de seguimiento.",
    ["gestor-servicios", "docker-compose", "operaciones-contenedores"],
    "moderate", true
  );
  addFunc(f, "ServiceManager.start", [23, 42], "Verifica la existencia del servicio y levanta sus contenedores en segundo plano con 'docker compose up -d'.", ["inicio-servicio", "compose-up", "ciclo-vida"], "simple", false);
  addFunc(f, "ServiceManager.stop", [45, 86], "Bloquea en modo read-only, previsualiza contenedores activos y exige confirmación para ejecutar 'docker compose down'.", ["detencion-servicio", "confirmacion-destructiva", "compose-down"], "moderate", false);
  addFunc(f, "ServiceManager.restart", [89, 109], "Reinicia los contenedores de un servicio existente mediante 'docker compose restart'.", ["reinicio-servicio", "compose-restart", "recuperacion"], "simple", false);
  addFunc(f, "ServiceManager.update", [112, 144], "Ejecuta 'docker compose pull' seguido de 'up -d --remove-orphans' bajo guardia read-only.", ["actualizacion-imagen", "compose-pull", "recreacion-contenedores"], "moderate", false);
  addFunc(f, "ServiceManager.logs", [147, 183], "Obtiene entre 1 y 500 líneas recientes de logs sin color y trunca salidas mayores a 8000 caracteres.", ["lectura-logs", "truncado-seguro", "diagnostico"], "moderate", false);
}

// ── 6. agent/tools/_shell.py ─────────────────────────────────────────────
{
  const f = "agent/tools/_shell.py";
  addFile(
    f,
    "Módulo base de seguridad para ejecutar subprocesos sin shell=True, validar nombres de servicio, resolver rutas y aplicar modos read-only/dry-run.",
    ["ejecucion-segura", "validacion-nombres", "prevencion-traversal", "modo-readonly"],
    "moderate",
    "Toda herramienta del agente debe delegar aquí en lugar de invocar subprocess con shell=True."
  );
  addClass(
    f, "InvalidServiceName", [42, 44],
    "Excepción de dominio lanzada cuando un nombre de servicio infringe las reglas de nomenclatura o intenta path traversal.",
    ["excepcion-seguridad", "validacion-input", "value-error"],
    "simple", true
  );
  addFunc(f, "validate_service_name", [47, 93], "Valida con expresión regular y lista de nombres reservados que el identificador de servicio no contenga traversal ni metacaracteres.", ["regex-seguridad", "nombres-reservados", "anti-inyeccion"], "moderate", true);
  addFunc(f, "validated_service_path", [96, 121], "Resuelve la ruta bajo /docker y verifica con relative_to que no escape del directorio base.", ["resolucion-rutas", "path-traversal", "pathlib"], "simple", true);
  addFunc(f, "safe_run", [129, 179], "Ejecuta listas de argumentos con shell=False y timeout controlado, o simula la ejecución cuando NAS_AGENT_DRYRUN está activo.", ["subproceso-seguro", "modo-dry-run", "control-timeout"], "moderate", true);
  addFunc(f, "find_compose", [187, 208], "Busca en el directorio validado del servicio cualquiera de los cuatro nombres estándar de archivo Docker Compose.", ["busqueda-compose", "convencion-archivos", "docker"], "simple", true);
  addFunc(f, "service_exists_or_error", [211, 240], "Comprueba que el servicio exista con compose válido y en caso contrario lista los servicios disponibles.", ["verificacion-servicio", "mensaje-error", "listado-disponibles"], "moderate", true);
  addFunc(f, "is_readonly", [257, 262], "Consulta la variable de entorno NAS_AGENT_READONLY para determinar si las acciones destructivas están bloqueadas.", ["modo-readonly", "variable-entorno", "seguridad"], "simple", true);
  addFunc(f, "is_dryrun", [265, 271], "Consulta la variable de entorno NAS_AGENT_DRYRUN para activar la simulación de comandos sin ejecución real.", ["modo-dry-run", "variable-entorno", "simulacion"], "simple", true);
  addFunc(f, "readonly_guard", [274, 291], "Devuelve un mensaje de bloqueo si el modo read-only está activo y la herramienta pertenece al conjunto destructivo.", ["guardia-seguridad", "herramientas-destructivas", "control-acceso"], "simple", true);
}

// ── 7. agent/tools/compose_tools.py ──────────────────────────────────────
{
  const f = "agent/tools/compose_tools.py";
  addFile(
    f,
    "Expone las tools Strands para leer, validar y generar desde cero la estructura completa de nuevos servicios Docker en /docker.",
    ["tools-compose", "generacion-servicios", "strands-tool", "plantillas-docker"],
    "complex",
    "Delega lectura y validación de forma perezosa a ComposeManager para evitar importaciones circulares."
  );
  addFunc(f, "read_compose", [32, 41], "Tool Strands que delega en ComposeManager.read para mostrar el compose completo de un servicio.", ["lectura-compose", "strands-tool", "wrapper-ligero"], "simple", true);
  addFunc(f, "validate_compose", [45, 55], "Tool Strands que delega en ComposeManager.validate para auditar un servicio contra las reglas del NAS.", ["validacion-compose", "strands-tool", "auditoria"], "simple", true);
  addFunc(f, "create_service", [59, 316], "Valida parámetros, verifica disponibilidad de puerto con ss, aplica anchors de _compose_base.md y genera compose.yml, .env y README.md.", ["creacion-servicio", "generacion-compose", "anchors-base", "validacion-puertos"], "complex", true);
}

// ── 8. agent/tools/diagnostic_tools.py ───────────────────────────────────
{
  const f = "agent/tools/diagnostic_tools.py";
  addFile(
    f,
    "Provee herramientas Strands de diagnóstico para supervisar salud global de contenedores, conflictos de puertos y fallos por servicio.",
    ["diagnostico-nas", "salud-contenedores", "conflictos-puertos", "strands-tool"],
    "moderate",
    "Combina invocaciones a 'svc health' / Docker CLI con parsing YAML directo de los archivos compose."
  );
  addFunc(f, "service_health", [25, 77], "Obtiene el tablero de salud vía 'svc health' o realiza fallback analizando 'docker ps -a' para detectar contenedores caídos o unhealthy.", ["tablero-salud", "monitoreo-docker", "fallback-cli"], "moderate", true);
  addFunc(f, "port_conflicts", [82, 138], "Escanea todos los archivos compose bajo /docker para construir un mapa de puertos e identificar colisiones.", ["deteccion-conflictos", "escaneo-puertos", "parsing-yaml"], "moderate", true);
  addFunc(f, "troubleshoot", [143, 241], "Inspecciona estado, healthcheck, cantidad de reinicios, consumo de recursos y errores en logs recientes para sugerir acciones.", ["troubleshooting", "inspeccion-contenedor", "analisis-logs"], "complex", true);
}

// ── 9. agent/tools/discovery_tools.py ────────────────────────────────────
{
  const f = "agent/tools/discovery_tools.py";
  addFile(
    f,
    "Implementa el descubrimiento de servicios desplegados en /docker y su exportación portable hacia agent/catalog/services/.",
    ["descubrimiento-servicios", "catalogo-docker", "sanitizacion-env", "strands-tool"],
    "complex",
    "Adapta rutas relativas de extends (_common.yml) y sanitiza secretos de .env antes de versionar en el catálogo."
  );
  addFunc(f, "_catalogize_compose_paths", [26, 38], "Reescribe referencias 'file: ../_common.yml' a '../../_common.yml' para ajustar la profundidad dentro del catálogo.", ["reescritura-rutas", "compose-extends", "catalogo"], "simple", false);
  addFunc(f, "list_services", [43, 96], "Recorre /docker identificando servicios con compose y consulta su estado activo o detenido.", ["inventario-servicios", "estado-compose", "listado-docker"], "moderate", true);
  addFunc(f, "scan_compose", [100, 192], "Analiza el archivo compose de un servicio extrayendo imagen, puertos, volúmenes, redes y variables redactadas.", ["inspeccion-compose", "redaccion-secretos", "parsing-yaml"], "moderate", true);
  addFunc(f, "auto_catalog", [196, 523], "Genera automáticamente el esqueleto ficha.md a partir del compose detectando variables ${VAR}, stacks multi-servicio y categoría.", ["auto-catalogacion", "generacion-ficha", "deteccion-stack"], "complex", true);
  addFunc(f, "bulk_discover", [528, 618], "Exporta masivamente todos los servicios de /docker mediante export_service y regenera el índice catalog.json.", ["exportacion-masiva", "indice-catalogo", "sincronizacion"], "moderate", true);
  addFunc(f, "export_service", [623, 750], "Copia compose.yml adaptado, .env.example sanitizado, README.md y ficha.md de un servicio hacia el catálogo versionable.", ["exportacion-servicio", "sanitizacion-secretos", "portabilidad-nas"], "complex", true);
}

// ── 10. agent/tools/search_tools.py ──────────────────────────────────────
{
  const f = "agent/tools/search_tools.py";
  addFile(
    f,
    "Busca información de configuración para servicios Docker no catalogados consultando la API pública de Docker Hub mediante curl.",
    ["busqueda-dockerhub", "descubrimiento-web", "extraccion-readme", "strands-tool"],
    "moderate",
    "Verifica primero el catálogo local antes de realizar consultas HTTP con safe_run(['curl', ...])."
  );
  addFunc(f, "search_service_info", [21, 74], "Comprueba si el servicio ya existe en el catálogo local y si no combina resultados de Docker Hub y READMEs oficiales.", ["busqueda-servicio", "consulta-catalogo", "api-dockerhub"], "moderate", true);
  addFunc(f, "_search_dockerhub", [77, 106], "Consulta el endpoint de búsqueda de repositorios de Docker Hub y formatea estrellas e imágenes oficiales.", ["api-dockerhub", "consulta-http", "curl-seguro"], "simple", false);
  addFunc(f, "_search_github_compose", [109, 130], "Obtiene la descripción completa desde los namespaces library y linuxserver en Docker Hub para extraer configuración.", ["metadatos-imagen", "linuxserver", "dockerhub-readme"], "simple", false);
  addFunc(f, "_extract_info_from_readme", [133, 155], "Extrae mediante expresiones regulares puertos, variables de entorno y rutas de volúmenes comunes de un README.", ["extraccion-regex", "analisis-readme", "puertos-volumenes"], "simple", false);
}

// ── 11. tests/test_compose_generation.py ─────────────────────────────────
{
  const f = "tests/test_compose_generation.py";
  addFile(
    f,
    "Suite de pruebas unitarias para sanitización de valores YAML, anchors base y carga de reglas en ComposeManager.",
    ["pruebas-unitarias", "pytest", "sanitizacion-yaml", "compose-manager"],
    "simple",
    "Valida el rechazo de traversal, caracteres de control y backticks mediante pytest.raises(InvalidServiceName)."
  );
  addClass(f, "TestComposeManagerSanitize", [8, 39], "Verifica la limpieza de espacios, aceptación de imágenes/volúmenes válidos y rechazo de entradas peligrosas en sanitize_value.", ["test-sanitizacion", "seguridad-yaml", "pytest"], "simple", true);
  addClass(f, "TestComposeManagerAnchors", [42, 57], "Comprueba que los anchors de respaldo y los extraídos de _compose_base.md incluyan los bloques obligatorios.", ["test-anchors", "plantilla-compose", "pytest"], "simple", true);
  addClass(f, "TestComposeManagerRules", [60, 69], "Verifica que load_rules retorne un diccionario válido con secciones nas y ports cuando existe _rules.md.", ["test-reglas", "catalogo-nas", "pytest"], "simple", true);
}

// ── 12. tests/test_memory.py ─────────────────────────────────────────────
{
  const f = "tests/test_memory.py";
  addFile(
    f,
    "Pruebas unitarias para el ciclo completo de MemoryManager usando fixtures aislados de directorio de memoria.",
    ["pruebas-unitarias", "sistema-memoria", "pytest", "fixtures-aislados"],
    "moderate",
    "Usa los fixtures isolate_memory y populated_memory para probar creación, búsqueda, curación y métricas sin tocar datos reales."
  );
  addClass(f, "TestEnsureInitialized", [12, 27], "Comprueba la creación inicial e idempotente de MEMORY.md, USER.md, SKILLS.md y sessions/.", ["test-inicializacion", "idempotencia", "pytest"], "simple", true);
  addClass(f, "TestAddToMemory", [30, 71], "Valida inserción por categoría, rechazo de categorías inválidas o textos largos, detección de duplicados y timestamp.", ["test-registro-memoria", "validacion-entradas", "pytest"], "simple", true);
  addClass(f, "TestRecall", [74, 102], "Prueba la búsqueda de contexto en memoria, skills y sesiones, además de consultas vacías o demasiado cortas.", ["test-busqueda", "recall-memoria", "pytest"], "simple", true);
  addClass(f, "TestAddSkill", [105, 128], "Verifica la creación de skills nuevos, prevención de duplicados e incremento del contador en SKILLS.md.", ["test-skills", "procedimientos", "pytest"], "simple", true);
  addClass(f, "TestUpdateUserModel", [131, 146], "Comprueba la adición de nuevas claves y actualización de preferencias existentes en USER.md.", ["test-perfil-usuario", "preferencias", "pytest"], "simple", true);
  addClass(f, "TestSaveSession", [149, 158], "Verifica la persistencia de resúmenes de sesión con nombre normalizado en sessions/.", ["test-sesiones", "persistencia-markdown", "pytest"], "simple", true);
  addClass(f, "TestCuration", [161, 190], "Prueba la eliminación de sesiones y entradas de MEMORY.md que exceden la antigüedad máxima.", ["test-curacion", "poda-antiguos", "pytest"], "simple", true);
  addClass(f, "TestMemoryStats", [193, 210], "Verifica la estructura y valores de estadísticas devueltas por get_memory_stats.", ["test-metricas", "estadisticas-memoria", "pytest"], "simple", true);
}

// ── 13. tests/test_result.py ─────────────────────────────────────────────
{
  const f = "tests/test_result.py";
  addFile(
    f,
    "Pruebas unitarias para ToolResult, Status y Timer verificando compatibilidad de conversión a string y medición temporal.",
    ["pruebas-unitarias", "tool-result", "cronometro-timer", "pytest"],
    "simple",
    "Cubre constructores ok/warn/error, serialización to_dict y márgenes de tiempo real con time.sleep."
  );
  addClass(f, "TestToolResult", [8, 67], "Valida constructores de estado, metadatos opcionales, valores por defecto, to_dict y compatibilidad __str__.", ["test-tool-result", "compatibilidad-strands", "pytest"], "simple", true);
  addClass(f, "TestTimer", [70, 83], "Comprueba que Timer mida intervalos positivos en milisegundos con y sin espera explícita.", ["test-timer", "medicion-tiempo", "pytest"], "simple", true);
}

// ── 14. tests/test_tool_result.py ────────────────────────────────────────
{
  const f = "tests/test_tool_result.py";
  addFile(
    f,
    "Pruebas complementarias para ToolResult y Timer organizadas por clase según estado, serialización y medición.",
    ["pruebas-unitarias", "tool-result", "serializacion", "pytest"],
    "simple",
    "Verifica también el formato de __repr__ junto con las variantes ok, error, warn y Timer."
  );
  addClass(f, "TestToolResultOk", [8, 24], "Valida éxito, conversión a string, datos adjuntos y sugerencias en ToolResult.ok.", ["test-estado-ok", "tool-result", "pytest"], "simple", true);
  addClass(f, "TestToolResultError", [27, 35], "Valida fallo booleano, estado ERROR y mensaje string en ToolResult.error.", ["test-estado-error", "tool-result", "pytest"], "simple", true);
  addClass(f, "TestToolResultWarn", [38, 42], "Valida que ToolResult.warn mantenga success=True con estado Status.WARNING.", ["test-estado-warning", "tool-result", "pytest"], "simple", true);
  addClass(f, "TestToolResultSerialization", [45, 58], "Comprueba la salida de to_dict y la representación legible __repr__ de ToolResult.", ["test-serializacion", "repr-dict", "pytest"], "simple", true);
  addClass(f, "TestTimer", [61, 67], "Verifica que Timer registre el tiempo transcurrido en milisegundos dentro de un bloque with.", ["test-timer", "cronometro", "pytest"], "simple", true);
}

// ── 15. tests/test_validation.py ─────────────────────────────────────────
{
  const f = "tests/test_validation.py";
  addFile(
    f,
    "Pruebas de seguridad unitarias para validate_service_name frente a path traversal e inyección de comandos.",
    ["pruebas-seguridad", "validacion-inputs", "anti-inyeccion", "pytest"],
    "simple",
    "Pruebas puras sin E/S que verifican nombres válidos y rechazos con InvalidServiceName."
  );
  addClass(f, "TestValidateServiceName", [16, 68], "Evalúa nombres válidos con guiones/números y el rechazo de traversal, rutas absolutas, espacios y metacaracteres shell.", ["test-validacion-nombre", "prevencion-traversal", "pytest"], "simple", true);
}

// ── Emit ALL imports strictly matching batchImportData ───────────────────
for (const [srcFile, targets] of Object.entries(batchImportData)) {
  for (const tgtFile of targets) {
    edges.push({
      source: `file:${srcFile}`,
      target: `file:${tgtFile}`,
      type: "imports",
      direction: "forward",
      weight: 0.7,
    });
  }
}

// ── Emit tested_by edges (ALWAYS production -> test) ─────────────────────
const testedByPairs = [
  ["agent/core/compose_manager.py", "tests/test_compose_generation.py", "Pruebas unitarias de sanitización, anchors y reglas"],
  ["agent/core/memory.py", "tests/test_memory.py", "Pruebas unitarias de inicialización, recall, skills y curación"],
  ["agent/core/_result.py", "tests/test_result.py", "Pruebas unitarias de ToolResult y Timer"],
  ["agent/core/_result.py", "tests/test_tool_result.py", "Pruebas unitarias por estado y serialización de ToolResult"],
  ["agent/tools/_shell.py", "tests/test_validation.py", "Pruebas de seguridad de validate_service_name"],
];
for (const [prod, test, desc] of testedByPairs) {
  edges.push({
    source: `file:${prod}`,
    target: `file:${test}`,
    type: "tested_by",
    direction: "forward",
    weight: 0.5,
    description: desc,
  });
}

// ── Emit verified calls edges ────────────────────────────────────────────
const fn = (p, n) => `function:${p}:${n}`;
const cl = (p, n) => `class:${p}:${n}`;

const R = "agent/core/_result.py";
const BM = "agent/core/backup_manager.py";
const CM = "agent/core/compose_manager.py";
const MM = "agent/core/memory.py";
const SM = "agent/core/service_manager.py";
const SH = "agent/tools/_shell.py";
const CT = "agent/tools/compose_tools.py";
const DT = "agent/tools/diagnostic_tools.py";
const DS = "agent/tools/discovery_tools.py";
const ST = "agent/tools/search_tools.py";

addCall(fn(BM, "BackupManager.backup"), fn(SH, "readonly_guard"));
addCall(fn(BM, "BackupManager.backup"), fn(SH, "validated_service_path"));
addCall(fn(BM, "BackupManager.backup"), fn(SH, "safe_run"));
addCall(fn(BM, "BackupManager.backup"), cl(R, "Timer"));
addCall(fn(BM, "BackupManager.backup"), fn(R, "ToolResult.error"));
addCall(fn(BM, "BackupManager.backup"), fn(R, "ToolResult.ok"));

addCall(fn(BM, "BackupManager.restore"), fn(SH, "readonly_guard"));
addCall(fn(BM, "BackupManager.restore"), fn(SH, "validate_service_name"));
addCall(fn(BM, "BackupManager.restore"), fn(SH, "safe_run"));
addCall(fn(BM, "BackupManager.restore"), cl(R, "Timer"));
addCall(fn(BM, "BackupManager.restore"), fn(R, "ToolResult.error"));
addCall(fn(BM, "BackupManager.restore"), fn(R, "ToolResult.warn"));
addCall(fn(BM, "BackupManager.restore"), fn(R, "ToolResult.ok"));

addCall(fn(BM, "BackupManager.list_all"), fn(R, "ToolResult.warn"));
addCall(fn(BM, "BackupManager.list_all"), fn(R, "ToolResult.ok"));

addCall(fn(CM, "ComposeManager.load_compose_base_anchors"), fn(CM, "ComposeManager._fallback_anchors"));
addCall(fn(CM, "ComposeManager.read"), fn(SH, "validate_service_name"));
addCall(fn(CM, "ComposeManager.read"), fn(SH, "find_compose"));
addCall(fn(CM, "ComposeManager.read"), fn(R, "ToolResult.error"));
addCall(fn(CM, "ComposeManager.read"), fn(R, "ToolResult.ok"));

addCall(fn(CM, "ComposeManager.validate"), fn(SH, "validate_service_name"));
addCall(fn(CM, "ComposeManager.validate"), fn(SH, "find_compose"));
addCall(fn(CM, "ComposeManager.validate"), fn(CM, "ComposeManager.load_rules"));
addCall(fn(CM, "ComposeManager.validate"), fn(SH, "validated_service_path"));
addCall(fn(CM, "ComposeManager.validate"), fn(SH, "safe_run"));
addCall(fn(CM, "ComposeManager.validate"), cl(R, "ToolResult"));
addCall(fn(CM, "ComposeManager.validate"), fn(R, "ToolResult.error"));
addCall(fn(CM, "ComposeManager.validate"), fn(R, "ToolResult.ok"));

for (const m of [
  "add_to_memory", "update_user_model", "add_skill",
  "save_session", "recall", "trim_sessions",
  "prune_old_entries", "get_memory_stats"
]) {
  addCall(fn(MM, `MemoryManager.${m}`), fn(MM, "MemoryManager.ensure_initialized"));
}
addCall(fn(MM, "MemoryManager.add_to_memory"), fn(R, "ToolResult.error"));
addCall(fn(MM, "MemoryManager.add_to_memory"), fn(R, "ToolResult.warn"));
addCall(fn(MM, "MemoryManager.add_to_memory"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.update_user_model"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.add_skill"), fn(R, "ToolResult.warn"));
addCall(fn(MM, "MemoryManager.add_skill"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.save_session"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.recall"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.trim_sessions"), fn(R, "ToolResult.ok"));
addCall(fn(MM, "MemoryManager.prune_old_entries"), fn(R, "ToolResult.ok"));

addCall(fn(SM, "ServiceManager.start"), fn(SH, "service_exists_or_error"));
addCall(fn(SM, "ServiceManager.start"), fn(SH, "find_compose"));
addCall(fn(SM, "ServiceManager.start"), fn(SH, "safe_run"));
addCall(fn(SM, "ServiceManager.start"), cl(R, "Timer"));
addCall(fn(SM, "ServiceManager.start"), fn(R, "ToolResult.error"));
addCall(fn(SM, "ServiceManager.start"), fn(R, "ToolResult.ok"));

addCall(fn(SM, "ServiceManager.stop"), fn(SH, "readonly_guard"));
addCall(fn(SM, "ServiceManager.stop"), fn(SH, "service_exists_or_error"));
addCall(fn(SM, "ServiceManager.stop"), fn(SH, "find_compose"));
addCall(fn(SM, "ServiceManager.stop"), fn(SH, "safe_run"));
addCall(fn(SM, "ServiceManager.stop"), cl(R, "Timer"));
addCall(fn(SM, "ServiceManager.stop"), fn(R, "ToolResult.error"));
addCall(fn(SM, "ServiceManager.stop"), fn(R, "ToolResult.warn"));
addCall(fn(SM, "ServiceManager.stop"), fn(R, "ToolResult.ok"));

addCall(fn(SM, "ServiceManager.restart"), fn(SH, "service_exists_or_error"));
addCall(fn(SM, "ServiceManager.restart"), fn(SH, "find_compose"));
addCall(fn(SM, "ServiceManager.restart"), fn(SH, "safe_run"));
addCall(fn(SM, "ServiceManager.restart"), cl(R, "Timer"));
addCall(fn(SM, "ServiceManager.restart"), fn(R, "ToolResult.error"));
addCall(fn(SM, "ServiceManager.restart"), fn(R, "ToolResult.ok"));

addCall(fn(SM, "ServiceManager.update"), fn(SH, "readonly_guard"));
addCall(fn(SM, "ServiceManager.update"), fn(SH, "service_exists_or_error"));
addCall(fn(SM, "ServiceManager.update"), fn(SH, "find_compose"));
addCall(fn(SM, "ServiceManager.update"), fn(SH, "safe_run"));
addCall(fn(SM, "ServiceManager.update"), cl(R, "Timer"));
addCall(fn(SM, "ServiceManager.update"), fn(R, "ToolResult.error"));
addCall(fn(SM, "ServiceManager.update"), fn(R, "ToolResult.ok"));

addCall(fn(SM, "ServiceManager.logs"), fn(SH, "service_exists_or_error"));
addCall(fn(SM, "ServiceManager.logs"), fn(SH, "find_compose"));
addCall(fn(SM, "ServiceManager.logs"), fn(SH, "safe_run"));
addCall(fn(SM, "ServiceManager.logs"), cl(R, "Timer"));
addCall(fn(SM, "ServiceManager.logs"), fn(R, "ToolResult.error"));
addCall(fn(SM, "ServiceManager.logs"), fn(R, "ToolResult.warn"));
addCall(fn(SM, "ServiceManager.logs"), fn(R, "ToolResult.ok"));

addCall(fn(SH, "validated_service_path"), fn(SH, "validate_service_name"));
addCall(fn(SH, "safe_run"), fn(SH, "is_dryrun"));
addCall(fn(SH, "find_compose"), fn(SH, "validated_service_path"));
addCall(fn(SH, "service_exists_or_error"), fn(SH, "validate_service_name"));
addCall(fn(SH, "service_exists_or_error"), fn(SH, "find_compose"));
addCall(fn(SH, "readonly_guard"), fn(SH, "is_readonly"));

addCall(fn(CT, "read_compose"), fn(CM, "ComposeManager.read"));
addCall(fn(CT, "validate_compose"), fn(CM, "ComposeManager.validate"));
addCall(fn(CT, "create_service"), fn(SH, "readonly_guard"));
addCall(fn(CT, "create_service"), fn(SH, "validated_service_path"));
addCall(fn(CT, "create_service"), fn(SH, "safe_run"));
addCall(fn(CT, "create_service"), fn(CM, "ComposeManager.load_rules"));
addCall(fn(CT, "create_service"), fn(CM, "ComposeManager.sanitize_value"));
addCall(fn(CT, "create_service"), fn(CM, "ComposeManager.load_compose_base_anchors"));
addCall(fn(CT, "create_service"), fn(R, "ToolResult.error"));
addCall(fn(CT, "create_service"), fn(R, "ToolResult.ok"));

addCall(fn(DT, "service_health"), fn(SH, "safe_run"));
addCall(fn(DT, "port_conflicts"), fn(SH, "validate_service_name"));
addCall(fn(DT, "port_conflicts"), fn(SH, "find_compose"));
addCall(fn(DT, "troubleshoot"), fn(SH, "service_exists_or_error"));
addCall(fn(DT, "troubleshoot"), fn(SH, "find_compose"));
addCall(fn(DT, "troubleshoot"), fn(SH, "safe_run"));

addCall(fn(DS, "list_services"), fn(SH, "validate_service_name"));
addCall(fn(DS, "list_services"), fn(SH, "find_compose"));
addCall(fn(DS, "list_services"), fn(SH, "safe_run"));
addCall(fn(DS, "scan_compose"), fn(SH, "validate_service_name"));
addCall(fn(DS, "scan_compose"), fn(SH, "find_compose"));
addCall(fn(DS, "auto_catalog"), fn(SH, "validate_service_name"));
addCall(fn(DS, "auto_catalog"), fn(SH, "find_compose"));
addCall(fn(DS, "bulk_discover"), fn(SH, "validate_service_name"));
addCall(fn(DS, "bulk_discover"), fn(SH, "find_compose"));
addCall(fn(DS, "bulk_discover"), fn(DS, "export_service"));
addCall(fn(DS, "bulk_discover"), cl(R, "Timer"));
addCall(fn(DS, "bulk_discover"), fn(R, "ToolResult.error"));
addCall(fn(DS, "bulk_discover"), fn(R, "ToolResult.warn"));
addCall(fn(DS, "bulk_discover"), fn(R, "ToolResult.ok"));
addCall(fn(DS, "export_service"), fn(SH, "validate_service_name"));
addCall(fn(DS, "export_service"), fn(SH, "find_compose"));
addCall(fn(DS, "export_service"), fn(DS, "_catalogize_compose_paths"));
addCall(fn(DS, "export_service"), fn(DS, "auto_catalog"));
addCall(fn(DS, "export_service"), fn(R, "ToolResult.error"));
addCall(fn(DS, "export_service"), fn(R, "ToolResult.ok"));

addCall(fn(ST, "search_service_info"), fn(SH, "validate_service_name"));
addCall(fn(ST, "search_service_info"), fn(ST, "_search_dockerhub"));
addCall(fn(ST, "search_service_info"), fn(ST, "_search_github_compose"));
addCall(fn(ST, "_search_dockerhub"), fn(SH, "safe_run"));
addCall(fn(ST, "_search_github_compose"), fn(SH, "safe_run"));
addCall(fn(ST, "_search_github_compose"), fn(ST, "_extract_info_from_readme"));

addCall(cl("tests/test_compose_generation.py", "TestComposeManagerSanitize"), fn(CM, "ComposeManager.sanitize_value"));
addCall(cl("tests/test_compose_generation.py", "TestComposeManagerAnchors"), fn(CM, "ComposeManager._fallback_anchors"));
addCall(cl("tests/test_compose_generation.py", "TestComposeManagerAnchors"), fn(CM, "ComposeManager.load_compose_base_anchors"));
addCall(cl("tests/test_compose_generation.py", "TestComposeManagerRules"), fn(CM, "ComposeManager.load_rules"));

addCall(cl("tests/test_memory.py", "TestEnsureInitialized"), fn(MM, "MemoryManager.ensure_initialized"));
addCall(cl("tests/test_memory.py", "TestAddToMemory"), fn(MM, "MemoryManager.add_to_memory"));
addCall(cl("tests/test_memory.py", "TestRecall"), fn(MM, "MemoryManager.recall"));
addCall(cl("tests/test_memory.py", "TestAddSkill"), fn(MM, "MemoryManager.add_skill"));
addCall(cl("tests/test_memory.py", "TestUpdateUserModel"), fn(MM, "MemoryManager.update_user_model"));
addCall(cl("tests/test_memory.py", "TestSaveSession"), fn(MM, "MemoryManager.save_session"));
addCall(cl("tests/test_memory.py", "TestCuration"), fn(MM, "MemoryManager.trim_sessions"));
addCall(cl("tests/test_memory.py", "TestCuration"), fn(MM, "MemoryManager.prune_old_entries"));
addCall(cl("tests/test_memory.py", "TestMemoryStats"), fn(MM, "MemoryManager.get_memory_stats"));

addCall(cl("tests/test_result.py", "TestToolResult"), cl(R, "ToolResult"));
addCall(cl("tests/test_result.py", "TestTimer"), cl(R, "Timer"));
addCall(cl("tests/test_tool_result.py", "TestToolResultOk"), fn(R, "ToolResult.ok"));
addCall(cl("tests/test_tool_result.py", "TestToolResultError"), fn(R, "ToolResult.error"));
addCall(cl("tests/test_tool_result.py", "TestToolResultWarn"), fn(R, "ToolResult.warn"));
addCall(cl("tests/test_tool_result.py", "TestToolResultSerialization"), fn(R, "ToolResult.to_dict"));
addCall(cl("tests/test_tool_result.py", "TestTimer"), cl(R, "Timer"));
addCall(cl("tests/test_validation.py", "TestValidateServiceName"), fn(SH, "validate_service_name"));

// ── Deduplicate & Validate ───────────────────────────────────────────────
const seenEdges = new Set();
const dedupEdges = [];
for (const e of edges) {
  if (e.source === e.target) throw new Error("Self-loop detected: " + e.source);
  const k = `${e.source}|${e.target}|${e.type}|${e.direction}`;
  if (!seenEdges.has(k)) {
    seenEdges.add(k);
    dedupEdges.push(e);
  }
}

const nodeIdSet = new Set(nodes.map((n) => n.id));
if (nodeIdSet.size !== nodes.length) throw new Error("Duplicate node ID detected");
for (const e of dedupEdges) {
  if (!nodeIdSet.has(e.source)) throw new Error("Missing edge source: " + e.source);
  if (!nodeIdSet.has(e.target)) throw new Error("Missing edge target: " + e.target);
}

const expectedImports = Object.values(batchImportData).reduce((s, a) => s + a.length, 0);
const actualImports = dedupEdges.filter((e) => e.type === "imports").length;
if (actualImports !== expectedImports) {
  throw new Error(`Imports mismatch: ${actualImports} vs ${expectedImports}`);
}

console.log(`Total nodes: ${nodes.length}, Total edges: ${dedupEdges.length}, Imports: ${actualImports}`);

// ── Split alphabetically by filePath into parts ──────────────────────────
const sortedFiles = batch2.files.map((f) => f.path).sort();
let parts = Math.ceil(Math.max(nodes.length / 60, dedupEdges.length / 120));
let partBuckets = [];
while (true) {
  const chunkSize = Math.ceil(sortedFiles.length / parts);
  partBuckets = [];
  let ok = true;
  for (let k = 0; k < parts; k++) {
    const chunkFiles = new Set(sortedFiles.slice(k * chunkSize, (k + 1) * chunkSize));
    if (chunkFiles.size === 0) continue;
    const partNodes = nodes.filter((n) => chunkFiles.has(n.filePath));
    const partNodeIds = new Set(partNodes.map((n) => n.id));
    const partEdges = dedupEdges.filter((e) => partNodeIds.has(e.source));
    if (partNodes.length > 60 || partEdges.length > 120) {
      ok = false;
      break;
    }
    partBuckets.push({ chunkFiles, partNodes, partEdges });
  }
  if (ok) break;
  parts++;
}
console.log(`Splitting into ${partBuckets.length} parts...`);

for (const existing of fs.readdirSync(outDir)) {
  if (/^batch-2(-part-\d+)?\.json$/.test(existing)) {
    fs.unlinkSync(path.join(outDir, existing));
  }
}

const partSummaries = [];
for (let k = 0; k < partBuckets.length; k++) {
  const { chunkFiles, partNodes, partEdges } = partBuckets[k];
  const outFile = path.join(outDir, `batch-2-part-${k + 1}.json`);
  const payload = { nodes: partNodes, edges: partEdges };
  fs.writeFileSync(outFile, JSON.stringify(payload, null, 2), "utf8");
  partSummaries.push({
    file: outFile,
    filesCount: chunkFiles.size,
    nodes: partNodes.length,
    edges: partEdges.length,
  });
}

console.log(JSON.stringify(partSummaries, null, 2));
