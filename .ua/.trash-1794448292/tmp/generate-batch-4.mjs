import fs from "fs";
import path from "path";

const INTERMEDIATE_DIR = "C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua/intermediate";

const nodes = [
  // =========================================================================
  // 1. agent/nas_agent.py
  // =========================================================================
  {
    id: "file:agent/nas_agent.py",
    type: "file",
    name: "nas_agent.py",
    filePath: "agent/nas_agent.py",
    lineRange: [1, 1399],
    summary: "Punto de entrada principal del agente inteligente del NAS basado en Strands Agents SDK. Gestiona configuración de entorno, sesiones persistentes, clasificación dinámica de prompts, selección de proveedor LLM y modos CLI/REPL.",
    tags: ["agente-ia", "strands-sdk", "prompt-dinamico", "cli-repl", "gestion-sesion"],
    complexity: "complex",
    languageNotes: "Módulo Python CLI con soporte multi-proveedor (Gemini, Bedrock, Ollama), renderizado opcional con Rich y persistencia de sesión via FileSessionManager."
  },
  {
    id: "function:agent/nas_agent.py:_load_env_agent",
    type: "function",
    name: "_load_env_agent",
    filePath: "agent/nas_agent.py",
    lineRange: [51, 68],
    summary: "Carga variables de entorno desde el archivo .env.agent sin sobrescribir las ya definidas en el entorno.",
    tags: ["configuracion", "variables-entorno", "inicializacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_get_session_metadata_path",
    type: "function",
    name: "_get_session_metadata_path",
    filePath: "agent/nas_agent.py",
    lineRange: [97, 99],
    summary: "Devuelve la ruta al archivo JSON de metadatos de la sesión actual del agente.",
    tags: ["gestion-sesion", "ruta-archivo", "metadatos"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_read_session_metadata",
    type: "function",
    name: "_read_session_metadata",
    filePath: "agent/nas_agent.py",
    lineRange: [102, 110],
    summary: "Lee y deserializa los metadatos JSON de la sesión actual devolviendo un diccionario vacío si falla o no existe.",
    tags: ["gestion-sesion", "lectura-json", "metadatos"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_write_session_metadata",
    type: "function",
    name: "_write_session_metadata",
    filePath: "agent/nas_agent.py",
    lineRange: [113, 117],
    summary: "Persiste los metadatos de la sesión en disco creando el directorio padre si es necesario.",
    tags: ["gestion-sesion", "escritura-json", "metadatos"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_session_is_expired",
    type: "function",
    name: "_session_is_expired",
    filePath: "agent/nas_agent.py",
    lineRange: [120, 126],
    summary: "Evalúa si la sesión actual ha superado el tiempo de inactividad configurado en SESSION_TIMEOUT_MIN.",
    tags: ["gestion-sesion", "expiracion-ttl", "validacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_clear_session",
    type: "function",
    name: "_clear_session",
    filePath: "agent/nas_agent.py",
    lineRange: [129, 133],
    summary: "Elimina recursivamente el directorio de sesiones y lo recrea vacío para reiniciar el contexto.",
    tags: ["gestion-sesion", "limpieza-estado", "archivos"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_get_session_manager",
    type: "function",
    name: "_get_session_manager",
    filePath: "agent/nas_agent.py",
    lineRange: [136, 161],
    summary: "Inicializa o reutiliza el FileSessionManager tras verificar expiración por timeout y actualizar contadores de turno.",
    tags: ["gestion-sesion", "strands-sdk", "persistencia"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:_load_catalog_summary",
    type: "function",
    name: "_load_catalog_summary",
    filePath: "agent/nas_agent.py",
    lineRange: [537, 589],
    summary: "Recorre las fichas del catálogo de servicios, extrae su frontmatter YAML y genera un resumen compacto para el prompt.",
    tags: ["catalogo-servicios", "parseo-yaml", "resumen-prompt"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:_get_catalog_block",
    type: "function",
    name: "_get_catalog_block",
    filePath: "agent/nas_agent.py",
    lineRange: [596, 610],
    summary: "Retorna el bloque de catálogo pre-cargado usando caché en memoria por invocación.",
    tags: ["catalogo-servicios", "cache-memoria", "prompt-dinamico"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_classify_query",
    type: "function",
    name: "_classify_query",
    filePath: "agent/nas_agent.py",
    lineRange: [617, 682],
    summary: "Pre-clasifica la consulta del usuario por palabras clave para seleccionar qué bloques temáticos cargar en el prompt del sistema.",
    tags: ["clasificacion-query", "prompt-dinamico", "enrutamiento"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:_assemble_prompt",
    type: "function",
    name: "_assemble_prompt",
    filePath: "agent/nas_agent.py",
    lineRange: [685, 709],
    summary: "Ensambla el prompt final del sistema combinando el bloque de pensamiento inicial con los bloques seleccionados.",
    tags: ["ensamblaje-prompt", "prompt-dinamico", "plantillas"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:get_model",
    type: "function",
    name: "get_model",
    filePath: "agent/nas_agent.py",
    lineRange: [715, 789],
    summary: "Instancia el modelo LLM correspondiente según NAS_AGENT_MODEL (Gemini, Bedrock con extended thinking u Ollama local).",
    tags: ["proveedores-llm", "gemini-bedrock-ollama", "configuracion-modelo"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:create_nas_agent",
    type: "function",
    name: "create_nas_agent",
    filePath: "agent/nas_agent.py",
    lineRange: [797, 854],
    summary: "Construye la instancia de Strands Agent con el modelo elegido, ALL_TOOLS, prompt dinámico y modo dry-run opcional.",
    tags: ["fabrica-agente", "strands-sdk", "dry-run"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:_switch_model",
    type: "function",
    name: "_switch_model",
    filePath: "agent/nas_agent.py",
    lineRange: [873, 937],
    summary: "Permite cambiar el modelo del agente por argumento o menú interactivo y persiste la selección en .env.agent.",
    tags: ["cambio-modelo", "menu-interactivo", "cli"],
    complexity: "moderate"
  },
  {
    id: "function:agent/nas_agent.py:_persist_model",
    type: "function",
    name: "_persist_model",
    filePath: "agent/nas_agent.py",
    lineRange: [940, 970],
    summary: "Actualiza o agrega NAS_AGENT_MODEL y NAS_AGENT_MODEL_ID dentro del archivo .env.agent.",
    tags: ["persistencia-config", "variables-entorno", "escritura-archivo"],
    complexity: "simple"
  },
  {
    id: "function:agent/nas_agent.py:_repl_mode",
    type: "function",
    name: "_repl_mode",
    filePath: "agent/nas_agent.py",
    lineRange: [978, 1154],
    summary: "Ejecuta el bucle conversacional interactivo (REPL) manteniendo el agente en memoria y manejando comandos internos como clear, status y exit.",
    tags: ["modo-repl", "bucle-conversacional", "interfaz-rich"],
    complexity: "complex"
  },
  {
    id: "function:agent/nas_agent.py:main",
    type: "function",
    name: "main",
    filePath: "agent/nas_agent.py",
    lineRange: [1162, 1395],
    summary: "Punto de entrada CLI que procesa flags (--new, --model, --clear, --status, --repl), ejecuta consultas únicas y renderiza respuestas.",
    tags: ["punto-entrada", "cli-principal", "manejo-errores"],
    complexity: "complex"
  },

  // =========================================================================
  // 2. agent/tools/__init__.py
  // =========================================================================
  {
    id: "file:agent/tools/__init__.py",
    type: "file",
    name: "__init__.py",
    filePath: "agent/tools/__init__.py",
    lineRange: [1, 110],
    summary: "Registro centralizado de herramientas del agente NAS que reexporta las funciones @tool en la lista ALL_TOOLS sin wrappers adicionales.",
    tags: ["registro-tools", "strands-sdk", "modulo-paquete"],
    complexity: "simple",
    languageNotes: "Reexporta 34 tools de 11 submódulos evitando decoradores envolventes porque Strands SDK exige funciones @tool puras."
  },

  // =========================================================================
  // 3. agent/tools/backup_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/backup_tools.py",
    type: "file",
    name: "backup_tools.py",
    filePath: "agent/tools/backup_tools.py",
    lineRange: [1, 54],
    summary: "Define las herramientas @tool de respaldo y restauración de servicios Docker delegando en BackupManager.",
    tags: ["tools-agente", "backup-restore", "servicios-docker"],
    complexity: "simple",
    languageNotes: "Usa importación perezosa en _get_backup_manager para prevenir dependencias circulares y decorador @tool de Strands."
  },
  {
    id: "function:agent/tools/backup_tools.py:_get_backup_manager",
    type: "function",
    name: "_get_backup_manager",
    filePath: "agent/tools/backup_tools.py",
    lineRange: [10, 13],
    summary: "Importa perezosamente y devuelve la clase BackupManager desde agent.core.backup_manager.",
    tags: ["lazy-import", "backup-manager", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/backup_tools.py:backup_service",
    type: "function",
    name: "backup_service",
    filePath: "agent/tools/backup_tools.py",
    lineRange: [17, 27],
    summary: "Tool que crea un respaldo comprimido con timestamp de los volúmenes y bind mounts de un servicio.",
    tags: ["tool-strands", "backup-servicio", "volumenes-docker"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/backup_tools.py:restore_service",
    type: "function",
    name: "restore_service",
    filePath: "agent/tools/backup_tools.py",
    lineRange: [31, 42],
    summary: "Tool que lista backups disponibles o restaura el más reciente cuando confirm='si'.",
    tags: ["tool-strands", "restauracion", "guard-confirmacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/backup_tools.py:list_backups",
    type: "function",
    name: "list_backups",
    filePath: "agent/tools/backup_tools.py",
    lineRange: [46, 54],
    summary: "Tool de solo lectura que enumera todos los backups existentes agrupados por servicio.",
    tags: ["tool-strands", "listado-backups", "solo-lectura"],
    complexity: "simple"
  },

  // =========================================================================
  // 4. agent/tools/capabilities.py
  // =========================================================================
  {
    id: "file:agent/tools/capabilities.py",
    type: "file",
    name: "capabilities.py",
    filePath: "agent/tools/capabilities.py",
    lineRange: [1, 124],
    summary: "Consulta el inventario dinámico de capacidades del NAS combinando manifests JSON versionados y el índice estructural del proyecto.",
    tags: ["inventario-capacidades", "manifests-json", "solo-lectura"],
    complexity: "moderate",
    languageNotes: "Carga dinámicamente agent/tools/project_index.py via importlib con fallback fail-closed al cache project-index.json."
  },
  {
    id: "function:agent/tools/capabilities.py:_manifests",
    type: "function",
    name: "_manifests",
    filePath: "agent/tools/capabilities.py",
    lineRange: [20, 27],
    summary: "Itera y parsea todos los archivos JSON en agent/capabilities/ adjuntando su ruta relativa.",
    tags: ["lectura-manifests", "json", "generador"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/capabilities.py:_index",
    type: "function",
    name: "_index",
    filePath: "agent/tools/capabilities.py",
    lineRange: [30, 48],
    summary: "Construye el índice estructural en vivo desde project_index.py o recurre al cache JSON si falla la importación.",
    tags: ["indice-proyecto", "carga-dinamica", "fallback-cache"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/capabilities.py:_operations",
    type: "function",
    name: "_operations",
    filePath: "agent/tools/capabilities.py",
    lineRange: [51, 81],
    summary: "Cruza las operaciones declaradas en manifests con el índice para reportar existencia de entrypoint, dispatch y guards.",
    tags: ["verificacion-contratos", "operaciones-cli", "fail-closed"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/capabilities.py:main",
    type: "function",
    name: "main",
    filePath: "agent/tools/capabilities.py",
    lineRange: [84, 120],
    summary: "CLI standalone que filtra operaciones por consulta o servicio y las imprime en texto o JSON.",
    tags: ["cli-standalone", "filtrado-capacidades", "salida-json"],
    complexity: "moderate"
  },

  // =========================================================================
  // 5. agent/tools/capability_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/capability_tools.py",
    type: "file",
    name: "capability_tools.py",
    filePath: "agent/tools/capability_tools.py",
    lineRange: [1, 47],
    summary: "Expone al agente la herramienta @tool discover_capabilities para consultar comandos reales sin ejecutar mutaciones.",
    tags: ["tools-agente", "descubrimiento-capacidades", "solo-lectura"],
    complexity: "simple",
    languageNotes: "Wrapper ligero de Strands @tool sobre agent.tools.capabilities._operations."
  },
  {
    id: "function:agent/tools/capability_tools.py:discover_capabilities",
    type: "function",
    name: "discover_capabilities",
    filePath: "agent/tools/capability_tools.py",
    lineRange: [13, 47],
    summary: "Busca operaciones reales en los manifests e índice filtrando por query y servicio, devolviendo guards y evidencias en JSON.",
    tags: ["tool-strands", "busqueda-comandos", "salida-json"],
    complexity: "simple"
  },

  // =========================================================================
  // 6. agent/tools/compare_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/compare_tools.py",
    type: "file",
    name: "compare_tools.py",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [1, 415],
    summary: "Detector de drift que compara archivos Docker Compose en producción contra el catálogo y la ficha del servicio.",
    tags: ["deteccion-drift", "docker-compose", "catalogo-servicios"],
    complexity: "complex",
    languageNotes: "Parsea YAML mediante análisis línea por línea y regex sin dependencia externa de PyYAML; soporta uso como @tool y CLI."
  },
  {
    id: "function:agent/tools/compare_tools.py:_compose_candidates",
    type: "function",
    name: "_compose_candidates",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [53, 59],
    summary: "Lista los archivos compose existentes de un servicio en orden de prioridad canónica.",
    tags: ["docker-compose", "resolucion-archivos", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_find_compose",
    type: "function",
    name: "_find_compose",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [62, 65],
    summary: "Selecciona el archivo compose principal de un servicio conservando la lista de candidatos ambiguos.",
    tags: ["docker-compose", "busqueda-archivo", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_discover_services",
    type: "function",
    name: "_discover_services",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [68, 81],
    summary: "Descubre nombres de servicios válidos en un directorio base por presencia de compose o ficha.md.",
    tags: ["descubrimiento-servicios", "directorio", "catalogo"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_extract_ports",
    type: "function",
    name: "_extract_ports",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [84, 101],
    summary: "Extrae los mapeos de puertos publicados desde el bloque ports de un archivo compose.",
    tags: ["parseo-compose", "puertos", "regex"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_extract_networks",
    type: "function",
    name: "_extract_networks",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [104, 127],
    summary: "Extrae las redes Docker declaradas dentro de la sección de servicio de un compose.",
    tags: ["parseo-compose", "redes-docker", "indentacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_extract_volumes",
    type: "function",
    name: "_extract_volumes",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [130, 146],
    summary: "Extrae los bind mounts y volúmenes con mapeo host:contenedor de un compose.",
    tags: ["parseo-compose", "volumenes", "almacenamiento"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_extract_env_vars",
    type: "function",
    name: "_extract_env_vars",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [149, 151],
    summary: "Extrae mediante regex las variables interpoladas con sintaxis ${VAR} en el compose.",
    tags: ["parseo-compose", "variables-entorno", "regex"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_extract_image",
    type: "function",
    name: "_extract_image",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [154, 157],
    summary: "Obtiene la imagen Docker principal definida en el archivo compose.",
    tags: ["parseo-compose", "imagen-docker", "regex"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_has_env_file_global",
    type: "function",
    name: "_has_env_file_global",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [160, 162],
    summary: "Comprueba si el compose referencia el archivo global ../.env.",
    tags: ["validacion-compose", "variables-entorno", "convenciones"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_has_healthcheck",
    type: "function",
    name: "_has_healthcheck",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [165, 167],
    summary: "Verifica si el compose incluye configuración de healthcheck.",
    tags: ["validacion-compose", "healthcheck", "convenciones"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_has_security_opt",
    type: "function",
    name: "_has_security_opt",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [170, 172],
    summary: "Verifica si el compose define security_opt o no-new-privileges.",
    tags: ["validacion-compose", "seguridad-docker", "convenciones"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_has_resource_limits",
    type: "function",
    name: "_has_resource_limits",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [175, 177],
    summary: "Comprueba si el compose establece límites de memoria o CPU.",
    tags: ["validacion-compose", "limites-recursos", "convenciones"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_parse_ficha_frontmatter",
    type: "function",
    name: "_parse_ficha_frontmatter",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [180, 200],
    summary: "Extrae pares clave-valor del frontmatter YAML de una ficha.md del catálogo.",
    tags: ["parseo-yaml", "ficha-servicio", "catalogo"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/compare_tools.py:_compare",
    type: "function",
    name: "_compare",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [208, 365],
    summary: "Compara el compose real con el del catálogo y su ficha, reportando drift de imagen, puertos, redes, volúmenes y convenciones pendientes.",
    tags: ["comparacion-config", "deteccion-drift", "reporte-servicio"],
    complexity: "complex"
  },
  {
    id: "function:agent/tools/compare_tools.py:compare_catalog",
    type: "function",
    name: "compare_catalog",
    filePath: "agent/tools/compare_tools.py",
    lineRange: [376, 388],
    summary: "Tool del agente que compara la configuración real de un servicio contra su entrada en el catálogo.",
    tags: ["tool-strands", "deteccion-drift", "comparacion-catalogo"],
    complexity: "simple"
  },

  // =========================================================================
  // 7. agent/tools/docker_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/docker_tools.py",
    type: "file",
    name: "docker_tools.py",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [1, 80],
    summary: "Provee herramientas @tool del agente para iniciar, detener, reiniciar, actualizar y consultar logs de servicios Docker.",
    tags: ["tools-agente", "control-docker", "ciclo-vida"],
    complexity: "simple",
    languageNotes: "Thin wrappers @tool que delegan mediante importación perezosa en agent.core.service_manager.ServiceManager."
  },
  {
    id: "function:agent/tools/docker_tools.py:_get_service_manager",
    type: "function",
    name: "_get_service_manager",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [10, 13],
    summary: "Importa perezosamente ServiceManager para evitar dependencias circulares.",
    tags: ["lazy-import", "service-manager", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/docker_tools.py:service_start",
    type: "function",
    name: "service_start",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [17, 27],
    summary: "Tool que levanta un servicio Docker ejecutando docker compose up -d.",
    tags: ["tool-strands", "iniciar-servicio", "docker-compose"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/docker_tools.py:service_stop",
    type: "function",
    name: "service_stop",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [31, 42],
    summary: "Tool destructiva que detiene un servicio Docker solo cuando confirm='si'.",
    tags: ["tool-strands", "detener-servicio", "guard-confirmacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/docker_tools.py:service_restart",
    type: "function",
    name: "service_restart",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [46, 54],
    summary: "Tool que reinicia los contenedores de un servicio sin destruirlos.",
    tags: ["tool-strands", "reiniciar-servicio", "docker-compose"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/docker_tools.py:service_update",
    type: "function",
    name: "service_update",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [58, 67],
    summary: "Tool que actualiza un servicio descargando su nueva imagen y recreando contenedores.",
    tags: ["tool-strands", "actualizar-servicio", "docker-compose"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/docker_tools.py:service_logs",
    type: "function",
    name: "service_logs",
    filePath: "agent/tools/docker_tools.py",
    lineRange: [71, 80],
    summary: "Tool de solo lectura que obtiene las últimas N líneas de logs de un servicio.",
    tags: ["tool-strands", "logs-contenedor", "diagnostico"],
    complexity: "simple"
  },

  // =========================================================================
  // 8. agent/tools/memory_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/memory_tools.py",
    type: "file",
    name: "memory_tools.py",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [1, 107],
    summary: "Expone herramientas @tool de memoria persistente y aprendizaje continuo (learning loop) delegando en MemoryManager.",
    tags: ["tools-agente", "memoria-persistente", "learning-loop"],
    complexity: "simple",
    languageNotes: "Delega en agent.core.memory.MemoryManager para leer y escribir MEMORY.md, USER.md, SKILLS.md y sesiones."
  },
  {
    id: "function:agent/tools/memory_tools.py:_mgr",
    type: "function",
    name: "_mgr",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [13, 16],
    summary: "Importa perezosamente y retorna la clase MemoryManager.",
    tags: ["lazy-import", "memory-manager", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:_now",
    type: "function",
    name: "_now",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [19, 20],
    summary: "Genera el timestamp ISO actual con precisión de segundos.",
    tags: ["timestamp", "fecha-hora", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:remember",
    type: "function",
    name: "remember",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [24, 38],
    summary: "Tool que persiste un hecho o lección aprendida bajo una categoría en MEMORY.md.",
    tags: ["tool-strands", "guardar-memoria", "aprendizaje"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:recall",
    type: "function",
    name: "recall",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [42, 54],
    summary: "Tool que busca conocimiento previo por prioridad en skills, memoria y sesiones.",
    tags: ["tool-strands", "consulta-memoria", "recuperacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:learn_skill",
    type: "function",
    name: "learn_skill",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [58, 70],
    summary: "Tool que registra un nuevo procedimiento reutilizable con su trigger en SKILLS.md.",
    tags: ["tool-strands", "skills-reutilizables", "aprendizaje"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:update_user_model",
    type: "function",
    name: "update_user_model",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [74, 85],
    summary: "Tool que actualiza preferencias observadas del usuario en USER.md.",
    tags: ["tool-strands", "perfil-usuario", "preferencias"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/memory_tools.py:memory_stats",
    type: "function",
    name: "memory_stats",
    filePath: "agent/tools/memory_tools.py",
    lineRange: [89, 107],
    summary: "Tool que formatea estadísticas de tamaño y uso de los archivos de memoria y sesiones.",
    tags: ["tool-strands", "estadisticas-memoria", "diagnostico"],
    complexity: "simple"
  },

  // =========================================================================
  // 9. agent/tools/project_scanner.py
  // =========================================================================
  {
    id: "file:agent/tools/project_scanner.py",
    type: "file",
    name: "project_scanner.py",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [1, 1201],
    summary: "Auditor integral del ecosistema nas-dotfiles que detecta inconsistencias entre servicios, higiene Compose, paridad CLI, prompt del agente, documentación y contratos arquitectónicos.",
    tags: ["auditoria-proyecto", "escaner-incremental", "contratos-arquitectura", "paridad-cli"],
    complexity: "complex",
    languageNotes: "Combina dataclasses (Snapshot, Issue, ScanResult), escaneo incremental basado en git diff, integración con project_index.py y modo dual @tool/CLI."
  },
  {
    id: "class:agent/tools/project_scanner.py:Snapshot",
    type: "class",
    name: "Snapshot",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [87, 121],
    summary: "Dataclass que persiste y carga en JSON el estado del último escaneo completo (commit, hashes y servicios).",
    tags: ["dataclass", "snapshot-estado", "persistencia-json"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_get_current_commit",
    type: "function",
    name: "_get_current_commit",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [124, 134],
    summary: "Obtiene el hash corto del commit HEAD actual mediante git rev-parse.",
    tags: ["git", "commit-head", "subproceso"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_get_changed_files",
    type: "function",
    name: "_get_changed_files",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [137, 183],
    summary: "Recopila archivos modificados, en staging y sin seguimiento desde un commit previo usando git diff y git ls-files.",
    tags: ["git-diff", "escaner-incremental", "archivos-cambiados"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_hash_file",
    type: "function",
    name: "_hash_file",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [186, 192],
    summary: "Calcula un hash MD5 corto del contenido de un archivo para detectar cambios.",
    tags: ["hash-md5", "integridad-archivo", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_classify_changed_file",
    type: "function",
    name: "_classify_changed_file",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [195, 261],
    summary: "Clasifica cada archivo modificado por categoría (servicio, CLI, agente, docs, etc.) para el escaneo incremental.",
    tags: ["clasificacion-archivos", "escaner-incremental", "enrutamiento"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_build_snapshot_from_scan",
    type: "function",
    name: "_build_snapshot_from_scan",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [264, 295],
    summary: "Construye un Snapshot con el commit actual, estado de servicios y hashes de archivos clave tras un escaneo.",
    tags: ["snapshot-estado", "hashes-archivo", "auditoria"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:incremental_scan",
    type: "function",
    name: "incremental_scan",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [298, 360],
    summary: "Ejecuta un escaneo selectivo analizando cambios en git respecto al snapshot previo y verificando solo las áreas afectadas.",
    tags: ["escaner-incremental", "git-diff", "optimizacion"],
    complexity: "moderate"
  },
  {
    id: "class:agent/tools/project_scanner.py:Issue",
    type: "class",
    name: "Issue",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [369, 382],
    summary: "Dataclass que representa una inconsistencia detectada con severidad, categoría, servicio afectado y sugerencia de corrección.",
    tags: ["dataclass", "modelo-issue", "diagnostico"],
    complexity: "simple"
  },
  {
    id: "class:agent/tools/project_scanner.py:ScanResult",
    type: "class",
    name: "ScanResult",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [386, 428],
    summary: "Dataclass agregadora del resultado del escaneo con conteos, lista de issues, estado de servicios y métricas arquitectónicas.",
    tags: ["dataclass", "resultado-scan", "serializacion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_detect_services",
    type: "function",
    name: "_detect_services",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [436, 458],
    summary: "Detecta todos los servicios Docker combinando directorios en DOCKER_BASE y entradas en el catálogo.",
    tags: ["descubrimiento-servicios", "docker", "catalogo"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_get_debmenux_scripts_dir",
    type: "function",
    name: "_get_debmenux_scripts_dir",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [461, 467],
    summary: "Resuelve el directorio de scripts de servicios de DebMenux entre la ruta principal y la alternativa.",
    tags: ["debmenux", "ruta-scripts", "integracion"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_services",
    type: "function",
    name: "_check_services",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [470, 551],
    summary: "Verifica por cada servicio la existencia de compose, ficha, guía, script DebMenux y etiquetas Homepage.",
    tags: ["verificacion-servicios", "documentacion", "debmenux"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_compose_hygiene",
    type: "function",
    name: "_check_compose_hygiene",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [554, 625],
    summary: "Audita los archivos Compose buscando IPs hardcodeadas, variables TZ duplicadas, falta de env_file y ausencia de healthcheck.",
    tags: ["higiene-compose", "auditoria-config", "seguridad"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_cli_parity",
    type: "function",
    name: "_check_cli_parity",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [628, 680],
    summary: "Compara los comandos registrados en svc.sh (Bash) contra svc_py/app.py (Python) para detectar divergencias de paridad.",
    tags: ["paridad-cli", "bash-python", "auditoria"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_agent_prompt",
    type: "function",
    name: "_check_agent_prompt",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [683, 730],
    summary: "Comprueba que los comandos reales de svc.sh estén documentados en BLOCK_CONTEXTO_NAS dentro de nas_agent.py.",
    tags: ["prompt-agente", "coherencia-cli", "auditoria"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_architecture_contracts",
    type: "function",
    name: "_check_architecture_contracts",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [733, 941],
    summary: "Valida el índice estructural generado por project_index.py frente a contracts.json, verificando manifests de capacidades, conexiones, contratos CLI y paridad con DebMenux.",
    tags: ["contratos-arquitectura", "indice-proyecto", "capacidades"],
    complexity: "complex"
  },
  {
    id: "function:agent/tools/project_scanner.py:_check_docs_references",
    type: "function",
    name: "_check_docs_references",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [949, 980],
    summary: "Comprueba que las rutas locales docs_url declaradas en las fichas de servicios apunten a archivos existentes.",
    tags: ["validacion-docs", "fichas-servicio", "enlaces-rotos"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:scan",
    type: "function",
    name: "scan",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [988, 999],
    summary: "Orquesta la ejecución completa de los seis validadores del proyecto y retorna un ScanResult.",
    tags: ["orquestacion-scan", "auditoria-completa", "scan-result"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:format_report",
    type: "function",
    name: "format_report",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [1002, 1081],
    summary: "Formatea el resultado del escaneo en un reporte legible con tabla de servicios, métricas arquitectónicas e issues agrupados por severidad.",
    tags: ["formateo-reporte", "salida-texto", "auditoria"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/project_scanner.py:project_scan",
    type: "function",
    name: "project_scan",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [1092, 1119],
    summary: "Tool del agente que ejecuta un escaneo completo o incremental del proyecto y devuelve el reporte formateado.",
    tags: ["tool-strands", "escaner-proyecto", "auditoria"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/project_scanner.py:main",
    type: "function",
    name: "main",
    filePath: "agent/tools/project_scanner.py",
    lineRange: [1143, 1197],
    summary: "Punto de entrada CLI de project_scanner con soporte para --verbose, --json, --full y --changed.",
    tags: ["cli-standalone", "escaner-proyecto", "salida-json"],
    complexity: "moderate"
  },

  // =========================================================================
  // 10. agent/tools/system_tools.py
  // =========================================================================
  {
    id: "file:agent/tools/system_tools.py",
    type: "file",
    name: "system_tools.py",
    filePath: "agent/tools/system_tools.py",
    lineRange: [1, 391],
    summary: "Herramientas @tool de diagnóstico del sistema operativo Linux e inspección segura de archivos del NAS.",
    tags: ["tools-agente", "diagnostico-sistema", "lectura-segura"],
    complexity: "moderate",
    languageNotes: "Ejecuta utilidades Linux (ss, df, free, ps, ip, docker, find, head) via safe_run y aplica sanitización de credenciales en archivos .env."
  },
  {
    id: "function:agent/tools/system_tools.py:scan_ports",
    type: "function",
    name: "scan_ports",
    filePath: "agent/tools/system_tools.py",
    lineRange: [14, 45],
    summary: "Tool que escanea puertos TCP/UDP ocupados con ss y sugiere los próximos 10 puertos libres en el rango 8100-8999.",
    tags: ["tool-strands", "puertos-red", "diagnostico"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/system_tools.py:_parse_ports",
    type: "function",
    name: "_parse_ports",
    filePath: "agent/tools/system_tools.py",
    lineRange: [48, 61],
    summary: "Extrae los números de puerto de la salida tabular del comando ss.",
    tags: ["parseo-salida", "puertos-red", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/system_tools.py:disk_usage",
    type: "function",
    name: "disk_usage",
    filePath: "agent/tools/system_tools.py",
    lineRange: [65, 105],
    summary: "Tool que consulta el espacio en disco de particiones físicas con df y genera alertas sobre 75% y 90%.",
    tags: ["tool-strands", "uso-disco", "alertas-sistema"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/system_tools.py:memory_info",
    type: "function",
    name: "memory_info",
    filePath: "agent/tools/system_tools.py",
    lineRange: [109, 151],
    summary: "Tool que reporta memoria RAM/swap con free, porcentaje de uso y los principales procesos consumidores.",
    tags: ["tool-strands", "memoria-ram", "procesos"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/system_tools.py:_calc_mem_pct",
    type: "function",
    name: "_calc_mem_pct",
    filePath: "agent/tools/system_tools.py",
    lineRange: [154, 171],
    summary: "Calcula el porcentaje entero de memoria usada a partir de la salida en bytes de free -b.",
    tags: ["calculo-memoria", "parseo-salida", "helper"],
    complexity: "simple"
  },
  {
    id: "function:agent/tools/system_tools.py:network_info",
    type: "function",
    name: "network_info",
    filePath: "agent/tools/system_tools.py",
    lineRange: [175, 223],
    summary: "Tool que muestra la IP principal, interfaces de red y redes custom de Docker con sus contenedores.",
    tags: ["tool-strands", "redes-docker", "interfaces-red"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/system_tools.py:list_files",
    type: "function",
    name: "list_files",
    filePath: "agent/tools/system_tools.py",
    lineRange: [228, 306],
    summary: "Tool que lista archivos y directorios mediante find validando rutas permitidas y bloqueando directorios sensibles.",
    tags: ["tool-strands", "exploracion-archivos", "lista-blanca"],
    complexity: "moderate"
  },
  {
    id: "function:agent/tools/system_tools.py:read_file_content",
    type: "function",
    name: "read_file_content",
    filePath: "agent/tools/system_tools.py",
    lineRange: [310, 391],
    summary: "Tool que lee archivos de texto dentro de rutas autorizadas limitando tamaño/líneas y redactando secretos en archivos .env.",
    tags: ["tool-strands", "lectura-archivos", "sanitizacion-secretos"],
    complexity: "moderate"
  },

  // =========================================================================
  // 11. tests/test_classify.py
  // =========================================================================
  {
    id: "file:tests/test_classify.py",
    type: "file",
    name: "test_classify.py",
    filePath: "tests/test_classify.py",
    lineRange: [1, 132],
    summary: "Suite de pruebas unitarias para la función pura _classify_query de agent/nas_agent.py organizada por intención de consulta.",
    tags: ["pruebas-unitarias", "pytest", "clasificacion-query"],
    complexity: "simple",
    languageNotes: "Pruebas basadas en clases pytest; depende de conftest.py para mockear Strands SDK durante la importación."
  },
  {
    id: "class:tests/test_classify.py:TestDiagnostico",
    type: "class",
    name: "TestDiagnostico",
    filePath: "tests/test_classify.py",
    lineRange: [11, 31],
    summary: "Agrupa casos de prueba para consultas de diagnóstico y fallos en servicios.",
    tags: ["suite-pruebas", "diagnostico", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestCreacion",
    type: "class",
    name: "TestCreacion",
    filePath: "tests/test_classify.py",
    lineRange: [34, 46],
    summary: "Agrupa casos de prueba para consultas de creación o instalación de nuevos servicios.",
    tags: ["suite-pruebas", "creacion-servicios", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestBackup",
    type: "class",
    name: "TestBackup",
    filePath: "tests/test_classify.py",
    lineRange: [49, 60],
    summary: "Agrupa casos de prueba para consultas de respaldo y restauración.",
    tags: ["suite-pruebas", "backup-restore", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestAdmin",
    type: "class",
    name: "TestAdmin",
    filePath: "tests/test_classify.py",
    lineRange: [63, 78],
    summary: "Agrupa casos de prueba para comandos de administración del ciclo de vida de servicios.",
    tags: ["suite-pruebas", "administracion-servicios", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestSistema",
    type: "class",
    name: "TestSistema",
    filePath: "tests/test_classify.py",
    lineRange: [81, 92],
    summary: "Agrupa casos de prueba para consultas sobre estado general, disco y puertos del sistema.",
    tags: ["suite-pruebas", "estado-sistema", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestIdentidad",
    type: "class",
    name: "TestIdentidad",
    filePath: "tests/test_classify.py",
    lineRange: [95, 103],
    summary: "Agrupa casos de prueba que verifican la carga mínima del bloque identidad.",
    tags: ["suite-pruebas", "identidad-agente", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestMemoria",
    type: "class",
    name: "TestMemoria",
    filePath: "tests/test_classify.py",
    lineRange: [106, 117],
    summary: "Agrupa casos de prueba para consultas relacionadas con memoria y skills guardados.",
    tags: ["suite-pruebas", "memoria-agente", "pytest"],
    complexity: "simple"
  },
  {
    id: "class:tests/test_classify.py:TestGeneral",
    type: "class",
    name: "TestGeneral",
    filePath: "tests/test_classify.py",
    lineRange: [120, 132],
    summary: "Agrupa casos de prueba para conversación general y garantías base de bloques cargados.",
    tags: ["suite-pruebas", "conversacion-general", "pytest"],
    complexity: "simple"
  }
];

const edges = [];

// Helper to push edge
function addEdge(source, target, type, weight, description) {
  if (source === target) return;
  edges.push({ source, target, type, direction: "forward", weight, description });
}

// 1. Auto-emit contains + exports for all symbol nodes
for (const n of nodes) {
  if (n.type === "function" || n.type === "class") {
    const fileId = `file:${n.filePath}`;
    addEdge(fileId, n.id, "contains", 1.0, `${n.filePath} contiene ${n.name}`);
    addEdge(fileId, n.id, "exports", 0.8, `${n.filePath} exporta ${n.name}`);
  }
}

// 2. Exact imports from batchImportData (15 edges)
const batchImports = {
  "agent/nas_agent.py": ["agent/tools/__init__.py"],
  "agent/tools/__init__.py": [
    "agent/tools/backup_tools.py",
    "agent/tools/capability_tools.py",
    "agent/tools/compare_tools.py",
    "agent/tools/compose_tools.py",
    "agent/tools/diagnostic_tools.py",
    "agent/tools/discovery_tools.py",
    "agent/tools/docker_tools.py",
    "agent/tools/memory_tools.py",
    "agent/tools/project_scanner.py",
    "agent/tools/search_tools.py",
    "agent/tools/system_tools.py"
  ],
  "agent/tools/capability_tools.py": ["agent/tools/capabilities.py"],
  "agent/tools/system_tools.py": ["agent/tools/_shell.py"],
  "tests/test_classify.py": ["agent/nas_agent.py"]
};

for (const [src, targets] of Object.entries(batchImports)) {
  for (const tgt of targets) {
    addEdge(`file:${src}`, `file:${tgt}`, "imports", 0.7, `${src} importa ${tgt}`);
  }
}

// 3. Intra-file & cross-file calls
const callEdges = [
  // agent/nas_agent.py
  ["function:agent/nas_agent.py:_read_session_metadata", "function:agent/nas_agent.py:_get_session_metadata_path", "Lee ruta de metadatos de sesión"],
  ["function:agent/nas_agent.py:_write_session_metadata", "function:agent/nas_agent.py:_get_session_metadata_path", "Obtiene ruta para persistir metadatos"],
  ["function:agent/nas_agent.py:_get_session_manager", "function:agent/nas_agent.py:_read_session_metadata", "Lee estado de sesión existente"],
  ["function:agent/nas_agent.py:_get_session_manager", "function:agent/nas_agent.py:_session_is_expired", "Verifica expiración de la sesión"],
  ["function:agent/nas_agent.py:_get_session_manager", "function:agent/nas_agent.py:_clear_session", "Limpia sesión expirada o forzada"],
  ["function:agent/nas_agent.py:_get_session_manager", "function:agent/nas_agent.py:_write_session_metadata", "Actualiza metadatos de actividad"],
  ["function:agent/nas_agent.py:_get_catalog_block", "function:agent/nas_agent.py:_load_catalog_summary", "Carga resumen de fichas al inicializar caché"],
  ["function:agent/nas_agent.py:_assemble_prompt", "function:agent/nas_agent.py:_get_catalog_block", "Inyecta bloque de catálogo pre-cargado"],
  ["function:agent/nas_agent.py:create_nas_agent", "function:agent/nas_agent.py:get_model", "Obtiene instancia del modelo LLM configurado"],
  ["function:agent/nas_agent.py:create_nas_agent", "function:agent/nas_agent.py:_classify_query", "Clasifica la consulta para seleccionar bloques"],
  ["function:agent/nas_agent.py:create_nas_agent", "function:agent/nas_agent.py:_assemble_prompt", "Ensambla el system prompt dinámico"],
  ["function:agent/nas_agent.py:_switch_model", "function:agent/nas_agent.py:_persist_model", "Persiste el nuevo modelo en .env.agent"],
  ["function:agent/nas_agent.py:_repl_mode", "function:agent/nas_agent.py:_get_session_manager", "Obtiene gestor de sesión para el REPL"],
  ["function:agent/nas_agent.py:_repl_mode", "function:agent/nas_agent.py:create_nas_agent", "Crea instancia del agente para conversación continua"],
  ["function:agent/nas_agent.py:_repl_mode", "function:agent/nas_agent.py:_clear_session", "Reinicia la sesión con el comando clear"],
  ["function:agent/nas_agent.py:_repl_mode", "function:agent/nas_agent.py:_read_session_metadata", "Consulta conteo de turnos en comando status"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_switch_model", "Cambia modelo cuando se pasa --model"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_clear_session", "Borra sesión cuando se pasa --clear"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_read_session_metadata", "Lee estado de sesión para --status"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_session_is_expired", "Evalúa expiración de sesión en --status"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_repl_mode", "Inicia bucle REPL cuando se pasa --repl o chat"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:_get_session_manager", "Inicializa FileSessionManager para consulta directa"],
  ["function:agent/nas_agent.py:main", "function:agent/nas_agent.py:create_nas_agent", "Construye el agente para ejecutar la query"],

  // agent/tools/backup_tools.py
  ["function:agent/tools/backup_tools.py:backup_service", "function:agent/tools/backup_tools.py:_get_backup_manager", "Resuelve BackupManager para respaldar"],
  ["function:agent/tools/backup_tools.py:restore_service", "function:agent/tools/backup_tools.py:_get_backup_manager", "Resuelve BackupManager para restaurar"],
  ["function:agent/tools/backup_tools.py:list_backups", "function:agent/tools/backup_tools.py:_get_backup_manager", "Resuelve BackupManager para listar backups"],

  // agent/tools/capabilities.py
  ["function:agent/tools/capabilities.py:_operations", "function:agent/tools/capabilities.py:_index", "Obtiene el índice estructural actualizado"],
  ["function:agent/tools/capabilities.py:_operations", "function:agent/tools/capabilities.py:_manifests", "Lee todos los manifests de capacidades"],
  ["function:agent/tools/capabilities.py:main", "function:agent/tools/capabilities.py:_operations", "Consulta operaciones para CLI de capacidades"],

  // agent/tools/capability_tools.py -> capabilities.py
  ["function:agent/tools/capability_tools.py:discover_capabilities", "function:agent/tools/capabilities.py:_operations", "Consulta operaciones registradas desde manifests e índice"],

  // agent/tools/compare_tools.py
  ["function:agent/tools/compare_tools.py:_find_compose", "function:agent/tools/compare_tools.py:_compose_candidates", "Lista archivos compose candidatos"],
  ["function:agent/tools/compare_tools.py:_discover_services", "function:agent/tools/compare_tools.py:_compose_candidates", "Detecta servicios con archivo compose"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_find_compose", "Localiza compose real y del catálogo"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_parse_ficha_frontmatter", "Extrae metadatos de ficha.md"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_extract_image", "Compara imagen Docker entre real y catálogo"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_extract_ports", "Compara puertos publicados"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_extract_networks", "Compara redes declaradas"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_extract_volumes", "Compara bind mounts y volúmenes"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_has_env_file_global", "Verifica env_file global ../.env"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_has_healthcheck", "Verifica presencia de healthcheck"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_has_security_opt", "Verifica configuración security_opt"],
  ["function:agent/tools/compare_tools.py:_compare", "function:agent/tools/compare_tools.py:_has_resource_limits", "Verifica límites de recursos"],
  ["function:agent/tools/compare_tools.py:compare_catalog", "function:agent/tools/compare_tools.py:_compare", "Ejecuta comparación real vs catálogo"],

  // agent/tools/docker_tools.py
  ["function:agent/tools/docker_tools.py:service_start", "function:agent/tools/docker_tools.py:_get_service_manager", "Obtiene ServiceManager para iniciar servicio"],
  ["function:agent/tools/docker_tools.py:service_stop", "function:agent/tools/docker_tools.py:_get_service_manager", "Obtiene ServiceManager para detener servicio"],
  ["function:agent/tools/docker_tools.py:service_restart", "function:agent/tools/docker_tools.py:_get_service_manager", "Obtiene ServiceManager para reiniciar servicio"],
  ["function:agent/tools/docker_tools.py:service_update", "function:agent/tools/docker_tools.py:_get_service_manager", "Obtiene ServiceManager para actualizar servicio"],
  ["function:agent/tools/docker_tools.py:service_logs", "function:agent/tools/docker_tools.py:_get_service_manager", "Obtiene ServiceManager para leer logs"],

  // agent/tools/memory_tools.py
  ["function:agent/tools/memory_tools.py:remember", "function:agent/tools/memory_tools.py:_mgr", "Accede a MemoryManager para guardar hecho"],
  ["function:agent/tools/memory_tools.py:remember", "function:agent/tools/memory_tools.py:_now", "Genera timestamp del aprendizaje"],
  ["function:agent/tools/memory_tools.py:recall", "function:agent/tools/memory_tools.py:_mgr", "Accede a MemoryManager para recuperar contexto"],
  ["function:agent/tools/memory_tools.py:learn_skill", "function:agent/tools/memory_tools.py:_mgr", "Accede a MemoryManager para registrar skill"],
  ["function:agent/tools/memory_tools.py:update_user_model", "function:agent/tools/memory_tools.py:_mgr", "Accede a MemoryManager para actualizar perfil"],
  ["function:agent/tools/memory_tools.py:memory_stats", "function:agent/tools/memory_tools.py:_mgr", "Accede a MemoryManager para métricas de tamaño"],

  // agent/tools/project_scanner.py
  ["function:agent/tools/project_scanner.py:_build_snapshot_from_scan", "function:agent/tools/project_scanner.py:_get_current_commit", "Registra el commit HEAD en el snapshot"],
  ["function:agent/tools/project_scanner.py:_build_snapshot_from_scan", "function:agent/tools/project_scanner.py:_hash_file", "Calcula hashes MD5 de archivos monitoreados"],
  ["function:agent/tools/project_scanner.py:incremental_scan", "function:agent/tools/project_scanner.py:scan", "Ejecuta scan completo si no hay snapshot previo"],
  ["function:agent/tools/project_scanner.py:incremental_scan", "function:agent/tools/project_scanner.py:_build_snapshot_from_scan", "Construye nuevo snapshot tras scan completo"],
  ["function:agent/tools/project_scanner.py:incremental_scan", "function:agent/tools/project_scanner.py:_get_changed_files", "Detecta archivos modificados via git diff"],
  ["function:agent/tools/project_scanner.py:incremental_scan", "function:agent/tools/project_scanner.py:_classify_changed_file", "Clasifica archivos modificados por dominio"],
  ["function:agent/tools/project_scanner.py:_check_services", "function:agent/tools/project_scanner.py:_detect_services", "Lista servicios existentes en local y catálogo"],
  ["function:agent/tools/project_scanner.py:_check_services", "function:agent/tools/project_scanner.py:_get_debmenux_scripts_dir", "Ubica scripts de servicios de DebMenux"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_services", "Verifica completitud de servicios"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_compose_hygiene", "Audita convenciones e higiene Compose"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_cli_parity", "Verifica paridad entre svc.sh y svc_py"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_agent_prompt", "Audita comandos en el prompt del agente"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_docs_references", "Valida enlaces locales docs_url"],
  ["function:agent/tools/project_scanner.py:scan", "function:agent/tools/project_scanner.py:_check_architecture_contracts", "Valida contratos contra el índice estructural"],
  ["function:agent/tools/project_scanner.py:project_scan", "function:agent/tools/project_scanner.py:scan", "Ejecuta escaneo completo cuando full=True o sin snapshot"],
  ["function:agent/tools/project_scanner.py:project_scan", "function:agent/tools/project_scanner.py:_build_snapshot_from_scan", "Construye snapshot para persistir estado"],
  ["function:agent/tools/project_scanner.py:project_scan", "function:agent/tools/project_scanner.py:incremental_scan", "Ejecuta escaneo incremental con snapshot existente"],
  ["function:agent/tools/project_scanner.py:project_scan", "function:agent/tools/project_scanner.py:format_report", "Formatea salida del escaneo para el agente"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:_get_changed_files", "Lista cambios en modo --changed"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:_classify_changed_file", "Clasifica cambios en modo --changed"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:scan", "Ejecuta escaneo completo en CLI"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:_build_snapshot_from_scan", "Actualiza snapshot tras escaneo CLI"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:incremental_scan", "Ejecuta escaneo incremental en CLI"],
  ["function:agent/tools/project_scanner.py:main", "function:agent/tools/project_scanner.py:format_report", "Imprime reporte legible en CLI"],

  // agent/tools/system_tools.py (intra-file + cross-batch to _shell.py)
  ["function:agent/tools/system_tools.py:scan_ports", "function:agent/tools/system_tools.py:_parse_ports", "Extrae puertos numéricos de la salida de ss"],
  ["function:agent/tools/system_tools.py:memory_info", "function:agent/tools/system_tools.py:_calc_mem_pct", "Calcula porcentaje usado de RAM desde free -b"],
  ["function:agent/tools/system_tools.py:scan_ports", "function:agent/tools/_shell.py:safe_run", "Ejecuta ss -tnlp y ss -unlp de forma segura"],
  ["function:agent/tools/system_tools.py:disk_usage", "function:agent/tools/_shell.py:safe_run", "Ejecuta df -h filtrado por tipo de filesystem"],
  ["function:agent/tools/system_tools.py:memory_info", "function:agent/tools/_shell.py:safe_run", "Ejecuta free y ps aux de forma segura"],
  ["function:agent/tools/system_tools.py:network_info", "function:agent/tools/_shell.py:safe_run", "Ejecuta hostname, ip y docker network"],
  ["function:agent/tools/system_tools.py:list_files", "function:agent/tools/_shell.py:safe_run", "Ejecuta find acotado por profundidad"],
  ["function:agent/tools/system_tools.py:read_file_content", "function:agent/tools/_shell.py:safe_run", "Ejecuta head para leer archivos autorizados"],

  // tests/test_classify.py -> nas_agent._classify_query
  ["file:tests/test_classify.py", "function:agent/nas_agent.py:_classify_query", "Ejercita _classify_query en todas las clases de prueba"]
];

for (const [src, tgt, desc] of callEdges) {
  addEdge(src, tgt, "calls", 0.8, desc);
}

// 4. depends_on & tested_by
addEdge(
  "file:agent/tools/project_scanner.py",
  "file:agent/nas_agent.py",
  "depends_on",
  0.6,
  "project_scanner inspecciona BLOCK_CONTEXTO_NAS en agent/nas_agent.py para validar paridad de comandos"
);
addEdge(
  "file:agent/tools/project_scanner.py",
  "file:agent/tools/__init__.py",
  "depends_on",
  0.6,
  "project_scanner referencia el registro de tools en agent/tools/__init__.py"
);
addEdge(
  "file:agent/nas_agent.py",
  "file:tests/test_classify.py",
  "tested_by",
  0.5,
  "tests/test_classify.py prueba la clasificación de consultas de agent/nas_agent.py"
);

// Validation before splitting
const nodeIds = new Set(nodes.map(n => n.id));
if (nodeIds.size !== nodes.length) {
  throw new Error("Duplicate node IDs detected!");
}
for (const n of nodes) {
  if (!["simple", "moderate", "complex"].includes(n.complexity)) {
    throw new Error(`Invalid complexity on ${n.id}: ${n.complexity}`);
  }
  if (!Array.isArray(n.tags) || n.tags.length < 3 || n.tags.length > 5) {
    throw new Error(`Invalid tags count on ${n.id}: ${JSON.stringify(n.tags)}`);
  }
  for (const t of n.tags) {
    if (!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(t)) {
      throw new Error(`Invalid tag format on ${n.id}: ${t}`);
    }
  }
}

// Split files alphabetically into parts
const filesSorted = [...new Set(nodes.map(n => n.filePath))].sort();
const partsCount = Math.ceil(Math.max(nodes.length / 60, edges.length / 120));
console.log(`Total nodes: ${nodes.length}, Total edges: ${edges.length}, partsCount: ${partsCount}`);

// Group files into partsCount chunks while ensuring every chunk respects <=60 nodes and <=120 edges
const fileStats = filesSorted.map(fp => {
  const fnodes = nodes.filter(n => n.filePath === fp);
  const fnodeIds = new Set(fnodes.map(n => n.id));
  const fedges = edges.filter(e => fnodeIds.has(e.source));
  return { fp, nodes: fnodes, edges: fedges };
});

// Try balanced greedy or equal-ish chunks preserving alphabetical order
const chunks = Array.from({ length: partsCount }, () => ({ files: [], nodes: [], edges: [] }));
// Equal-ish index split first, adjust if needed
let fileIdx = 0;
for (let p = 0; p < partsCount; p++) {
  const remainingParts = partsCount - p;
  const remainingFiles = fileStats.length - fileIdx;
  while (fileIdx < fileStats.length) {
    const f = fileStats[fileIdx];
    const fits = (chunks[p].nodes.length + f.nodes.length <= 60) && (chunks[p].edges.length + f.edges.length <= 120);
    // Leave at least 1 file for each remaining part if possible
    const mustLeave = remainingParts - 1;
    const filesLeftAfterThis = fileStats.length - (fileIdx + 1);
    if (p < partsCount - 1 && chunks[p].files.length > 0) {
      // Check if next part can take the rest, or target ~1/partsCount of edges
      const targetEdges = edges.length / partsCount;
      if (!fits || (chunks[p].edges.length >= targetEdges * 0.85 && filesLeftAfterThis >= mustLeave)) {
        break;
      }
    }
    if (!fits && chunks[p].files.length > 0) break;
    chunks[p].files.push(f.fp);
    chunks[p].nodes.push(...f.nodes);
    chunks[p].edges.push(...f.edges);
    fileIdx++;
  }
}

if (fileIdx !== fileStats.length) {
  throw new Error(`Not all files assigned! Assigned ${fileIdx}/${fileStats.length}`);
}

for (let i = 0; i < chunks.length; i++) {
  const c = chunks[i];
  console.log(`Part ${i + 1}: files=${c.files.length} (${c.files.join(", ")}), nodes=${c.nodes.length}, edges=${c.edges.length}`);
  if (c.nodes.length > 60 || c.edges.length > 120) {
    throw new Error(`Part ${i + 1} exceeds limits! nodes=${c.nodes.length}, edges=${c.edges.length}`);
  }
  const outPath = path.join(INTERMEDIATE_DIR, `batch-4-part-${i + 1}.json`);
  const payload = {
    batchIndex: 4,
    part: i + 1,
    totalParts: chunks.length,
    nodes: c.nodes,
    edges: c.edges
  };
  fs.writeFileSync(outPath, JSON.stringify(payload, null, 2), "utf8");
}

console.log("Successfully wrote all batch-4 parts.");
