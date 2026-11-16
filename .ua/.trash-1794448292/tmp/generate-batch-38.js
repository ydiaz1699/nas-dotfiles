const fs = require('fs');
const path = require('path');

const OUT_DIR = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua/intermediate';

// Orden alfabético de los 25 archivos del batch 38
const files = [
  {
    path: 'agent/catalog/services/usb-api/ficha.md',
    nodes: [
      {
        id: 'document:agent/catalog/services/usb-api/ficha.md',
        type: 'document',
        name: 'ficha.md',
        filePath: 'agent/catalog/services/usb-api/ficha.md',
        summary: 'Documentación de ficha del catálogo para el servicio nativo systemd usb-api, que expone una API REST en el puerto 8091 para listar y desmontar unidades USB desde el widget de Homepage.',
        tags: ['catalogo-servicios', 'usb-api', 'systemd', 'api-rest', 'homepage'],
        complexity: 'simple',
        languageNotes: 'Documento Markdown con frontmatter YAML de metadatos del servicio y ejemplos JSON de respuesta.'
      }
    ],
    edges: [
      {
        source: 'document:agent/catalog/services/usb-api/ficha.md',
        target: 'document:docs/services/ntfy-guide.md',
        type: 'related',
        direction: 'forward',
        weight: 0.5
      }
    ]
  },
  {
    path: 'agent/config/__init__.py',
    nodes: [
      {
        id: 'file:agent/config/__init__.py',
        type: 'file',
        name: '__init__.py',
        filePath: 'agent/config/__init__.py',
        summary: 'Archivo marcador que define agent/config como paquete Python para la configuración del agente NAS.',
        tags: ['paquete-python', 'configuracion', 'agente-nas'],
        complexity: 'simple',
        languageNotes: 'Módulo Python mínimo con comentario identificador de paquete.'
      }
    ],
    edges: []
  },
  {
    path: 'agent/config/defaults.yml',
    nodes: [
      {
        id: 'config:agent/config/defaults.yml',
        type: 'config',
        name: 'defaults.yml',
        filePath: 'agent/config/defaults.yml',
        summary: 'Configuración por defecto del agente NAS en YAML, definiendo plugins habilitados, historial de eventos, parámetros MQTT, scheduler, caché, sesiones y logging.',
        tags: ['configuracion-yaml', 'agente-nas', 'mqtt', 'scheduler'],
        complexity: 'simple',
        languageNotes: 'Archivo YAML de valores base sobreescribibles mediante .env.agent o variables de entorno.'
      }
    ],
    edges: [
      {
        source: 'config:agent/config/defaults.yml',
        target: 'file:agent/daemon.py',
        type: 'configures',
        direction: 'forward',
        weight: 0.6
      }
    ]
  },
  {
    path: 'agent/core/__init__.py',
    nodes: [
      {
        id: 'file:agent/core/__init__.py',
        type: 'file',
        name: '__init__.py',
        filePath: 'agent/core/__init__.py',
        summary: 'Inicializador del paquete agent.core, que documenta la capa de lógica de negocio reutilizable y desacoplada de los wrappers @tool del agente NAS.',
        tags: ['paquete-core', 'logica-negocio', 'agente-nas'],
        complexity: 'simple',
        languageNotes: 'Solo contiene el docstring arquitectónico del paquete sin importaciones ni símbolos ejecutables.'
      }
    ],
    edges: [
      {
        source: 'file:agent/core/__init__.py',
        target: 'file:agent/core/service_manager.py',
        type: 'related',
        direction: 'forward',
        weight: 0.5
      },
      {
        source: 'file:agent/core/__init__.py',
        target: 'file:agent/core/compose_manager.py',
        type: 'related',
        direction: 'forward',
        weight: 0.5
      },
      {
        source: 'file:agent/core/__init__.py',
        target: 'file:agent/core/backup_manager.py',
        type: 'related',
        direction: 'forward',
        weight: 0.5
      }
    ]
  },
  {
    path: 'agent/daemon.py',
    nodes: [
      {
        id: 'file:agent/daemon.py',
        type: 'file',
        name: 'daemon.py',
        filePath: 'agent/daemon.py',
        summary: 'Punto de entrada en modo daemon (systemd) del agente NAS; carga .env.agent, descubre plugins, ejecuta tareas periódicas con Scheduler y gestiona señales SIGTERM/SIGINT.',
        tags: ['daemon', 'systemd', 'scheduler', 'agente-nas', 'senales'],
        complexity: 'moderate',
        languageNotes: 'Usa threading.Thread y threading.Event para programar tareas periódicas y apagar el proceso de forma controlada.'
      },
      {
        id: 'function:agent/daemon.py:_load_env_agent',
        type: 'function',
        name: '_load_env_agent',
        filePath: 'agent/daemon.py',
        lineRange: [35, 49],
        summary: 'Lee el archivo .env.agent en la raíz del proyecto e inyecta sus pares clave-valor en os.environ sin sobreescribir variables existentes.',
        tags: ['variables-entorno', 'env-agent', 'inicializacion'],
        complexity: 'simple'
      },
      {
        id: 'class:agent/daemon.py:Scheduler',
        type: 'class',
        name: 'Scheduler',
        filePath: 'agent/daemon.py',
        lineRange: [66, 130],
        summary: 'Ejecutor thread-safe de tareas periódicas en hilos daemon separados con intervalos configurables y parada controlada mediante threading.Event.',
        tags: ['scheduler', 'multihilo', 'tareas-periodicas'],
        complexity: 'moderate'
      },
      {
        id: 'class:agent/daemon.py:NASAgentDaemon',
        type: 'class',
        name: 'NASAgentDaemon',
        filePath: 'agent/daemon.py',
        lineRange: [136, 215],
        summary: 'Orquestador principal del daemon del agente NAS; inicializa PluginLoader, registra schedules de plugins, ejecuta el heartbeat de memoria y espera señales de parada.',
        tags: ['daemon', 'orquestador', 'plugins', 'heartbeat'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/daemon.py:_signal_handler',
        type: 'function',
        name: '_signal_handler',
        filePath: 'agent/daemon.py',
        lineRange: [223, 228],
        summary: 'Manejador de señales SIGTERM y SIGINT que registra la señal recibida y solicita la detención ordenada de la instancia activa de NASAgentDaemon.',
        tags: ['senales-so', 'shutdown-graceful', 'daemon'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/daemon.py:main',
        type: 'function',
        name: 'main',
        filePath: 'agent/daemon.py',
        lineRange: [234, 243],
        summary: 'Punto de entrada CLI que registra los manejadores de señales, instancia NASAgentDaemon e inicia el bucle principal del daemon.',
        tags: ['entrypoint', 'daemon', 'cli'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:_load_env_agent', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:_load_env_agent', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/daemon.py', target: 'class:agent/daemon.py:Scheduler', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/daemon.py', target: 'class:agent/daemon.py:Scheduler', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/daemon.py', target: 'class:agent/daemon.py:NASAgentDaemon', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/daemon.py', target: 'class:agent/daemon.py:NASAgentDaemon', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:_signal_handler', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:_signal_handler', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:main', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/daemon.py', target: 'function:agent/daemon.py:main', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/daemon.py:NASAgentDaemon', target: 'class:agent/daemon.py:Scheduler', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/daemon.py:_signal_handler', target: 'class:agent/daemon.py:NASAgentDaemon', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/daemon.py:main', target: 'class:agent/daemon.py:NASAgentDaemon', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/daemon.py', target: 'file:agent/plugins/__init__.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/daemon.py', target: 'file:agent/core/memory.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/daemon.py', target: 'file:tests/test_daemon.py', type: 'tested_by', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'agent/lobehub_mcp.py',
    nodes: [
      {
        id: 'file:agent/lobehub_mcp.py',
        type: 'file',
        name: 'lobehub_mcp.py',
        filePath: 'agent/lobehub_mcp.py',
        summary: 'Gateway MCP read-only estrecho para LobeHub con soporte de transporte HTTP, stdio y helper sobre Unix socket, validación de origen/token Bearer y redacción de datos sensibles.',
        tags: ['gateway-mcp', 'lobehub', 'solo-lectura', 'json-rpc', 'unix-socket'],
        complexity: 'complex',
        languageNotes: 'Implementado únicamente con la biblioteca estándar de Python (http.server, socket, subprocess, hmac) y una allowlist estricta de operaciones.'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_json_bytes',
        type: 'function',
        name: '_json_bytes',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [80, 81],
        summary: 'Serializa un valor Python a bytes UTF-8 en formato JSON compacto sin espacios innecesarios.',
        tags: ['serializacion-json', 'helper', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_redact_text',
        type: 'function',
        name: '_redact_text',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [84, 89],
        summary: 'Sanitiza cadenas reemplazando rutas internas, direcciones IP y tokens Bearer por marcadores redactados y limita la longitud a 500 caracteres.',
        tags: ['redaccion', 'seguridad', 'sanitizacion'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_audit_path',
        type: 'function',
        name: '_audit_path',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [92, 96],
        summary: 'Determina la ruta del archivo JSONL de auditoría usando MCP_AUDIT_LOG o el valor por defecto en ~/.nas-agent.',
        tags: ['auditoria', 'configuracion-ruta', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:audit',
        type: 'function',
        name: 'audit',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [99, 124],
        summary: 'Escribe registros JSONL de auditoría con permisos restrictivos 0600 incluyendo evento, herramienta, resultado y duración sin registrar secretos ni argumentos.',
        tags: ['auditoria', 'jsonl', 'permisos-archivo'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_error',
        type: 'function',
        name: '_error',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [127, 128],
        summary: 'Construye un diccionario estándar de error MCP con los campos ok, error y message.',
        tags: ['manejo-errores', 'respuesta-mcp', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_check_lines',
        type: 'function',
        name: '_check_lines',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [131, 148],
        summary: 'Extrae y clasifica líneas de verificación (ok, warn, error) desde stdout sanitizado de comandos svc lobehub.',
        tags: ['parsing-salida', 'diagnostico', 'redaccion'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_status_services',
        type: 'function',
        name: '_status_services',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [151, 181],
        summary: 'Parsea la salida tabular de svc lobehub status extrayendo servicio, estado y salud de contenedores permitidos.',
        tags: ['parsing-salida', 'estado-contenedores', 'lobehub'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_safe_capabilities',
        type: 'function',
        name: '_safe_capabilities',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [184, 253],
        summary: 'Lee los manifests de agent/capabilities/*.json y verifica en solo lectura que las operaciones expuestas existan, tengan guard válido y no sean mutaciones.',
        tags: ['capacidades', 'manifests-json', 'solo-lectura'],
        complexity: 'complex'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_run_svc',
        type: 'function',
        name: '_run_svc',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [256, 311],
        summary: 'Ejecuta de forma controlada docker/cli/svc.sh lobehub con una acción fija y devuelve checks o estado de servicios sanitizados.',
        tags: ['subproceso', 'svc-cli', 'solo-lectura', 'lobehub'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_local_operation',
        type: 'function',
        name: '_local_operation',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [314, 320],
        summary: 'Despacha localmente una operación de la allowlist hacia _safe_capabilities o _run_svc.',
        tags: ['despachador', 'allowlist', 'operacion-local'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_helper_request',
        type: 'function',
        name: '_helper_request',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [323, 348],
        summary: 'Envía una solicitud JSON de una línea al helper host mediante Unix socket (AF_UNIX) respetando timeout y tamaño máximo.',
        tags: ['unix-socket', 'cliente-ipc', 'timeout'],
        complexity: 'moderate'
      },
      {
        id: 'class:agent/lobehub_mcp.py:Gateway',
        type: 'class',
        name: 'Gateway',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [351, 374],
        summary: 'Fachada de ejecución MCP que valida operaciones contra TOOL_NAMES, rechaza argumentos del cliente, delega al helper socket o ejecución local y audita cada llamada.',
        tags: ['gateway-mcp', 'validacion', 'auditoria'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_tool_schema',
        type: 'function',
        name: '_tool_schema',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [377, 386],
        summary: 'Genera el esquema MCP de una herramienta publicada declarando inputSchema vacío sin propiedades adicionales.',
        tags: ['esquema-mcp', 'json-schema', 'tools'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_rpc_result',
        type: 'function',
        name: '_rpc_result',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [389, 390],
        summary: 'Construye una respuesta exitosa JSON-RPC 2.0.',
        tags: ['json-rpc', 'respuesta', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_rpc_error',
        type: 'function',
        name: '_rpc_error',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [393, 394],
        summary: 'Construye un objeto de error estándar JSON-RPC 2.0 con código y mensaje.',
        tags: ['json-rpc', 'error', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:handle_rpc',
        type: 'function',
        name: 'handle_rpc',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [397, 435],
        summary: 'Procesa mensajes JSON-RPC 2.0 del protocolo MCP (initialize, notifications, ping, tools/list y tools/call) delegando las llamadas al Gateway.',
        tags: ['json-rpc', 'protocolo-mcp', 'router'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_origin_allowed',
        type: 'function',
        name: '_origin_allowed',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [438, 447],
        summary: 'Valida la cabecera HTTP Origin contra la lista MCP_ALLOWED_ORIGINS permitiendo peticiones server-to-server sin Origin.',
        tags: ['cors', 'seguridad-http', 'origin'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_authorized',
        type: 'function',
        name: '_authorized',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [450, 455],
        summary: 'Verifica autenticación Bearer en tiempo constante usando hmac.compare_digest frente a MCP_SERVICE_TOKEN.',
        tags: ['autenticacion-bearer', 'hmac', 'seguridad-http'],
        complexity: 'simple'
      },
      {
        id: 'class:agent/lobehub_mcp.py:MCPHTTPHandler',
        type: 'class',
        name: 'MCPHTTPHandler',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [458, 558],
        summary: 'Manejador HTTP para Streamable MCP con endpoints /health y /mcp, control CORS, autenticación Bearer y soporte para OPTIONS, GET y POST.',
        tags: ['servidor-http', 'mcp', 'cors', 'bearer-auth'],
        complexity: 'complex'
      },
      {
        id: 'function:agent/lobehub_mcp.py:run_http',
        type: 'function',
        name: 'run_http',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [561, 581],
        summary: 'Levanta ThreadingHTTPServer en host y puerto configurados tras validar la presencia obligatoria de MCP_SERVICE_TOKEN.',
        tags: ['servidor-http', 'transporte-mcp', 'daemon'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:_helper_client',
        type: 'function',
        name: '_helper_client',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [584, 614],
        summary: 'Atiende una conexión entrante de Unix socket en el modo helper leyendo la operación solicitada y devolviendo la respuesta JSON.',
        tags: ['unix-socket', 'helper-host', 'ipc'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/lobehub_mcp.py:run_helper',
        type: 'function',
        name: 'run_helper',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [617, 683],
        summary: 'Inicia el servidor Unix socket del helper host asignando GID y permisos 0660, despachando clientes en hilos daemon y gestionando SIGTERM/SIGINT.',
        tags: ['unix-socket', 'helper-host', 'seguridad-permisos', 'systemd'],
        complexity: 'complex'
      },
      {
        id: 'function:agent/lobehub_mcp.py:run_stdio',
        type: 'function',
        name: 'run_stdio',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [686, 701],
        summary: 'Ejecuta el servidor MCP sobre stdin/stdout leyendo peticiones JSON-RPC delimitadas por salto de línea.',
        tags: ['transporte-stdio', 'json-rpc', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/lobehub_mcp.py:main',
        type: 'function',
        name: 'main',
        filePath: 'agent/lobehub_mcp.py',
        lineRange: [704, 714],
        summary: 'Punto de entrada CLI que analiza --mode o MCP_MODE (http, helper, stdio) y arranca el transporte correspondiente.',
        tags: ['entrypoint', 'cli', 'mcp'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_json_bytes', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_json_bytes', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_redact_text', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_redact_text', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_audit_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_audit_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:audit', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:audit', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_error', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_error', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_check_lines', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_check_lines', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_status_services', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_status_services', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_safe_capabilities', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_safe_capabilities', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_run_svc', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_run_svc', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_local_operation', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_local_operation', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_helper_request', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_helper_request', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'class:agent/lobehub_mcp.py:Gateway', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'class:agent/lobehub_mcp.py:Gateway', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_tool_schema', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_tool_schema', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_rpc_result', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_rpc_result', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_rpc_error', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_rpc_error', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:handle_rpc', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:handle_rpc', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_origin_allowed', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_origin_allowed', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_authorized', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_authorized', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_http', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_http', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_helper_client', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:_helper_client', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_helper', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_helper', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_stdio', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:run_stdio', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:main', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/lobehub_mcp.py', target: 'function:agent/lobehub_mcp.py:main', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:audit', target: 'function:agent/lobehub_mcp.py:_audit_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_check_lines', target: 'function:agent/lobehub_mcp.py:_redact_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_safe_capabilities', target: 'function:agent/lobehub_mcp.py:_redact_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_safe_capabilities', target: 'function:agent/lobehub_mcp.py:audit', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_run_svc', target: 'function:agent/lobehub_mcp.py:_check_lines', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_run_svc', target: 'function:agent/lobehub_mcp.py:_status_services', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_run_svc', target: 'function:agent/lobehub_mcp.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_local_operation', target: 'function:agent/lobehub_mcp.py:_safe_capabilities', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_local_operation', target: 'function:agent/lobehub_mcp.py:_run_svc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_helper_request', target: 'function:agent/lobehub_mcp.py:_json_bytes', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_helper_request', target: 'function:agent/lobehub_mcp.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:Gateway', target: 'function:agent/lobehub_mcp.py:_helper_request', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:Gateway', target: 'function:agent/lobehub_mcp.py:_local_operation', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:Gateway', target: 'function:agent/lobehub_mcp.py:audit', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:handle_rpc', target: 'function:agent/lobehub_mcp.py:_tool_schema', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:handle_rpc', target: 'function:agent/lobehub_mcp.py:_rpc_result', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:handle_rpc', target: 'function:agent/lobehub_mcp.py:_rpc_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', target: 'function:agent/lobehub_mcp.py:_origin_allowed', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', target: 'function:agent/lobehub_mcp.py:_authorized', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', target: 'function:agent/lobehub_mcp.py:handle_rpc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', target: 'function:agent/lobehub_mcp.py:_json_bytes', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:run_http', target: 'class:agent/lobehub_mcp.py:MCPHTTPHandler', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:_helper_client', target: 'function:agent/lobehub_mcp.py:_json_bytes', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:run_helper', target: 'function:agent/lobehub_mcp.py:_helper_client', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:run_stdio', target: 'function:agent/lobehub_mcp.py:handle_rpc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:main', target: 'class:agent/lobehub_mcp.py:Gateway', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:main', target: 'function:agent/lobehub_mcp.py:run_http', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:main', target: 'function:agent/lobehub_mcp.py:run_helper', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/lobehub_mcp.py:main', target: 'function:agent/lobehub_mcp.py:run_stdio', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/lobehub_mcp.py', target: 'file:docker/cli/svc.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/lobehub_mcp.py', target: 'config:agent/capabilities/lobehub.json', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
    nodes: [
      {
        id: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        type: 'file',
        name: 'nas_mcp_gateway.py',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        summary: 'Front-door MCP read-only con activación lazy de worker para nas-dotfiles; publica herramientas del manifest en modo stdio o HTTP y apaga el worker tras inactividad.',
        tags: ['gateway-mcp', 'lazy-worker', 'json-rpc', 'solo-lectura'],
        complexity: 'complex',
        languageNotes: 'Usa selectors, subprocess.Popen, threading y ThreadingHTTPServer de la biblioteca estándar para supervisar el ciclo de vida del worker.'
      },
      {
        id: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:ManifestError',
        type: 'class',
        name: 'ManifestError',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [32, 33],
        summary: 'Excepción lanzada cuando el manifest JSON de nas-mcp-gateway es inválido o no coincide con la allowlist del worker.',
        tags: ['excepcion', 'validacion-manifest', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_manifest_path',
        type: 'function',
        name: '_manifest_path',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [36, 38],
        summary: 'Obtiene la ruta al manifest JSON desde NAS_MCP_MANIFEST o usa nas_mcp_manifest.json junto al módulo.',
        tags: ['configuracion-ruta', 'manifest', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest',
        type: 'function',
        name: 'load_manifest',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [41, 70],
        summary: 'Carga y valida el manifest canónico de herramientas comprobando metadatos del servidor, duplicados y concordancia exacta con OPERATIONS del worker.',
        tags: ['validacion-manifest', 'allowlist', 'mcp'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error',
        type: 'function',
        name: '_error',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [73, 74],
        summary: 'Genera una estructura estándar de error del gateway con ok=False, código y mensaje.',
        tags: ['manejo-errores', 'respuesta-mcp', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_json_bytes',
        type: 'function',
        name: '_json_bytes',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [77, 78],
        summary: 'Serializa un objeto Python a bytes UTF-8 en JSON compacto.',
        tags: ['serializacion-json', 'helper', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_tool_schema',
        type: 'function',
        name: '_tool_schema',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [81, 89],
        summary: 'Convierte una entrada de herramienta del manifest al formato tools/list del protocolo MCP.',
        tags: ['esquema-mcp', 'tools', 'manifest'],
        complexity: 'simple'
      },
      {
        id: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:WorkerSupervisor',
        type: 'class',
        name: 'WorkerSupervisor',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [92, 207],
        summary: 'Supervisa el subproceso nas_mcp_worker.py bajo demanda; lo arranca en el primer request, lee respuestas con timeout vía selectors y lo termina tras inactividad.',
        tags: ['supervisor-procesos', 'lazy-worker', 'timeout', 'multihilo'],
        complexity: 'complex'
      },
      {
        id: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway',
        type: 'class',
        name: 'Gateway',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [210, 226],
        summary: 'Coordina el catálogo del manifest con WorkerSupervisor validando que las llamadas no reciban argumentos y aplicando el timeout configurado.',
        tags: ['gateway-mcp', 'validacion', 'orquestacion'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_result',
        type: 'function',
        name: '_rpc_result',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [229, 230],
        summary: 'Empaqueta un resultado JSON-RPC 2.0 válido.',
        tags: ['json-rpc', 'respuesta', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error',
        type: 'function',
        name: '_rpc_error',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [233, 234],
        summary: 'Empaqueta un error JSON-RPC 2.0 con código y descripción.',
        tags: ['json-rpc', 'error', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc',
        type: 'function',
        name: 'handle_rpc',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [237, 275],
        summary: 'Despacha métodos JSON-RPC 2.0 del estándar MCP (initialize, ping, notifications, tools/list y tools/call) contra el Gateway.',
        tags: ['json-rpc', 'protocolo-mcp', 'router'],
        complexity: 'moderate'
      },
      {
        id: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer',
        type: 'class',
        name: 'StdioServer',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [278, 301],
        summary: 'Servidor MCP sobre entrada y salida estándar que valida límites de tamaño de petición/respuesta y cierra el Gateway al finalizar.',
        tags: ['transporte-stdio', 'json-rpc', 'mcp'],
        complexity: 'simple'
      },
      {
        id: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler',
        type: 'class',
        name: 'HTTPHandler',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [304, 374],
        summary: 'Manejador HTTP para nas-mcp-gateway con /health, verificación de Origin, autenticación Bearer en tiempo constante y endpoint POST JSON-RPC.',
        tags: ['servidor-http', 'bearer-auth', 'cors', 'mcp'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:run_http',
        type: 'function',
        name: 'run_http',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [377, 397],
        summary: 'Arranca ThreadingHTTPServer para nas-mcp-gateway verificando MCP_SERVICE_TOKEN y cerrando el Gateway al detenerse.',
        tags: ['servidor-http', 'transporte-mcp', 'daemon'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main',
        type: 'function',
        name: 'main',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        lineRange: [400, 413],
        summary: 'Entrypoint CLI que carga el manifest, construye el Gateway e inicia el modo stdio o http según argumentos o NAS_MCP_MODE.',
        tags: ['entrypoint', 'cli', 'mcp'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:ManifestError', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:ManifestError', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_manifest_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_manifest_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_json_bytes', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_json_bytes', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_tool_schema', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_tool_schema', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:WorkerSupervisor', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:WorkerSupervisor', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_result', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_result', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:run_http', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:run_http', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_manifest_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:ManifestError', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:WorkerSupervisor', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:WorkerSupervisor', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_tool_schema', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_result', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_json_bytes', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:handle_rpc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_json_bytes', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:_rpc_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:run_http', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:HTTPHandler', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:load_manifest', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:Gateway', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:run_http', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:main', target: 'class:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py:StdioServer', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py', target: 'config:agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json',
    nodes: [
      {
        id: 'config:agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json',
        type: 'config',
        name: 'nas_mcp_manifest.json',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json',
        summary: 'Manifest canónico JSON de nas-mcp-gateway que declara el modo de activación lazy-worker, el tiempo de inactividad, la ruta del Unix socket y las cuatro herramientas read-only expuestas.',
        tags: ['manifest-json', 'mcp-gateway', 'lazy-worker', 'solo-lectura'],
        complexity: 'simple',
        languageNotes: 'Define esquemas JSON Schema sin propiedades adicionales para nas_services, nas_health, nas_capabilities y nas_diagnostics.'
      }
    ],
    edges: [
      {
        source: 'config:agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json',
        target: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_gateway.py',
        type: 'configures',
        direction: 'forward',
        weight: 0.6
      },
      {
        source: 'config:agent/mcp/nas_mcp_gateway/nas_mcp_manifest.json',
        target: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        type: 'configures',
        direction: 'forward',
        weight: 0.6
      }
    ]
  },
  {
    path: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
    nodes: [
      {
        id: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        type: 'file',
        name: 'nas_mcp_worker.py',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        summary: 'Worker y helper host read-only de nas-mcp-gateway; en modo client reenvía operaciones permitidas por Unix socket y en modo helper ejecuta comandos fijos de svc.sh con salida redactada y auditoría.',
        tags: ['worker-mcp', 'unix-socket', 'solo-lectura', 'auditoria', 'redaccion'],
        complexity: 'complex',
        languageNotes: 'Aplica expresiones regulares para redactar rutas, IPs y credenciales antes de devolver la salida de svc.sh.'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error',
        type: 'function',
        name: '_error',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [39, 40],
        summary: 'Devuelve un diccionario estándar de error para respuestas del worker o helper.',
        tags: ['manejo-errores', 'worker-mcp', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_redact',
        type: 'function',
        name: '_redact',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [43, 48],
        summary: 'Enmascara rutas del sistema, direcciones IP, tokens Bearer y pares clave=valor sensibles truncando la línea a MAX_OUTPUT_LINE_BYTES.',
        tags: ['redaccion', 'seguridad', 'sanitizacion'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_safe_output',
        type: 'function',
        name: '_safe_output',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [51, 55],
        summary: 'Aplica _redact a las primeras MAX_OUTPUT_LINES líneas de stdout y añade marcador si la salida fue truncada.',
        tags: ['sanitizacion', 'truncado-salida', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_audit',
        type: 'function',
        name: '_audit',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [58, 79],
        summary: 'Registra en MCP_AUDIT_LOG eventos JSONL con timestamp UTC, operación, resultado y duración protegiendo el archivo con permisos 0600.',
        tags: ['auditoria', 'jsonl', 'permisos-archivo'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc',
        type: 'function',
        name: '_run_fixed_svc',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [82, 136],
        summary: 'Ejecuta únicamente operaciones de la allowlist OPERATIONS invocando docker/cli/svc.sh con argumentos fijos, timeout y SVC_DOCTOR_NO_HISTORY=1 en diagnósticos.',
        tags: ['svc-cli', 'subproceso', 'solo-lectura', 'allowlist'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_socket_path',
        type: 'function',
        name: '_socket_path',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [139, 140],
        summary: 'Resuelve la ruta del Unix socket desde MCP_HELPER_SOCKET o usa DEFAULT_SOCKET.',
        tags: ['unix-socket', 'configuracion-ruta', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request',
        type: 'function',
        name: '_helper_request',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [143, 168],
        summary: 'Conecta por Unix socket AF_UNIX al helper host enviando una operación permitida y decodificando la respuesta JSON de una línea.',
        tags: ['unix-socket', 'cliente-ipc', 'timeout'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop',
        type: 'function',
        name: '_client_loop',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [171, 190],
        summary: 'Lee peticiones JSON línea a línea desde stdin, valida que contengan únicamente la clave operation y las reenvía a _helper_request.',
        tags: ['ipc-stdio', 'worker-client', 'validacion'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper',
        type: 'function',
        name: '_serve_helper',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [193, 271],
        summary: 'Escucha en el Unix socket con grupo MCP_SOCKET_GID y permisos 0660, atendiendo peticiones válidas mediante _run_fixed_svc hasta recibir SIGTERM/SIGINT.',
        tags: ['unix-socket', 'helper-host', 'systemd', 'seguridad-permisos'],
        complexity: 'complex'
      },
      {
        id: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:main',
        type: 'function',
        name: 'main',
        filePath: 'agent/mcp/nas_mcp_gateway/nas_mcp_worker.py',
        lineRange: [274, 280],
        summary: 'Punto de entrada CLI que selecciona entre el modo client y el modo helper mediante el argumento --mode.',
        tags: ['entrypoint', 'cli', 'worker-mcp'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_redact', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_redact', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_safe_output', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_safe_output', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_audit', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_audit', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_socket_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_socket_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:main', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:main', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_safe_output', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_redact', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_audit', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_safe_output', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_socket_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_helper_request', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_socket_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_error', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_run_fixed_svc', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:main', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_serve_helper', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:main', target: 'function:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py:_client_loop', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/mcp/nas_mcp_gateway/nas_mcp_worker.py', target: 'file:docker/cli/svc.sh', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'agent/memory/sessions/.gitkeep',
    nodes: [
      {
        id: 'file:agent/memory/sessions/.gitkeep',
        type: 'file',
        name: '.gitkeep',
        filePath: 'agent/memory/sessions/.gitkeep',
        summary: 'Archivo marcador vacío para preservar el directorio de almacenamiento de sesiones de memoria del agente en Git.',
        tags: ['gitkeep', 'memoria-sesiones', 'marcador-directorio'],
        complexity: 'simple',
        languageNotes: 'Archivo vacío sin contenido ejecutable.'
      }
    ],
    edges: []
  },
  {
    path: 'agent/tools/_audit.py',
    nodes: [
      {
        id: 'file:agent/tools/_audit.py',
        type: 'file',
        name: '_audit.py',
        filePath: 'agent/tools/_audit.py',
        summary: 'Sistema de auditoría en formato JSON Lines para herramientas del agente NAS; registra marca temporal, argumentos sanitizados, vista previa del resultado y duración, incluyendo el decorador @audited.',
        tags: ['auditoria', 'decorador', 'jsonl', 'sanitizacion', 'tools-agente'],
        complexity: 'moderate',
        languageNotes: 'Usa functools.wraps, inspect.signature y time.perf_counter para envolver funciones @tool sin interrumpir la ejecución ante errores de E/S.'
      },
      {
        id: 'function:agent/tools/_audit.py:_get_log_path',
        type: 'function',
        name: '_get_log_path',
        filePath: 'agent/tools/_audit.py',
        lineRange: [36, 38],
        summary: 'Obtiene la ruta del archivo de auditoría desde NAS_AGENT_AUDIT_LOG o usa /docker/backups/agent_audit.log por defecto.',
        tags: ['auditoria', 'configuracion-ruta', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/tools/_audit.py:_is_audit_enabled',
        type: 'function',
        name: '_is_audit_enabled',
        filePath: 'agent/tools/_audit.py',
        lineRange: [41, 43],
        summary: 'Comprueba la variable NAS_AGENT_AUDIT para determinar si el registro de auditoría está activo.',
        tags: ['auditoria', 'feature-flag', 'helper'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/tools/_audit.py:log_tool_call',
        type: 'function',
        name: 'log_tool_call',
        filePath: 'agent/tools/_audit.py',
        lineRange: [51, 106],
        summary: 'Añade una entrada JSON Line al archivo de auditoría con timestamp UTC, argumentos sanitizados, resultado truncado, duración y posible error, usando fallback en HOME si falta permiso.',
        tags: ['auditoria', 'jsonl', 'logging'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/tools/_audit.py:_sanitize_args',
        type: 'function',
        name: '_sanitize_args',
        filePath: 'agent/tools/_audit.py',
        lineRange: [109, 118],
        summary: 'Enmascara claves sensibles como password, token, secret o api_key y recorta cadenas largas en los argumentos registrados.',
        tags: ['sanitizacion', 'seguridad', 'auditoria'],
        complexity: 'simple'
      },
      {
        id: 'function:agent/tools/_audit.py:audited',
        type: 'function',
        name: 'audited',
        filePath: 'agent/tools/_audit.py',
        lineRange: [126, 172],
        summary: 'Decorador que mide el tiempo de ejecución de una herramienta @tool, captura excepciones y registra la llamada mediante log_tool_call.',
        tags: ['decorador', 'auditoria', 'telemetria'],
        complexity: 'moderate'
      },
      {
        id: 'function:agent/tools/_audit.py:get_session_summary',
        type: 'function',
        name: 'get_session_summary',
        filePath: 'agent/tools/_audit.py',
        lineRange: [180, 223],
        summary: 'Lee las últimas N entradas válidas del audit log y construye un resumen legible con fecha, estado, herramienta y duración.',
        tags: ['auditoria', 'resumen-sesion', 'jsonl'],
        complexity: 'moderate'
      }
    ],
    edges: [
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_get_log_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_get_log_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_is_audit_enabled', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_is_audit_enabled', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:log_tool_call', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:log_tool_call', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_sanitize_args', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:_sanitize_args', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:audited', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:audited', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:get_session_summary', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_audit.py', target: 'function:agent/tools/_audit.py:get_session_summary', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/_audit.py:log_tool_call', target: 'function:agent/tools/_audit.py:_is_audit_enabled', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/_audit.py:log_tool_call', target: 'function:agent/tools/_audit.py:_get_log_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/_audit.py:log_tool_call', target: 'function:agent/tools/_audit.py:_sanitize_args', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/_audit.py:audited', target: 'function:agent/tools/_audit.py:log_tool_call', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/_audit.py:get_session_summary', target: 'function:agent/tools/_audit.py:_get_log_path', type: 'calls', direction: 'forward', weight: 0.8 }
    ]
  },
  {
    path: 'agent/tools/_result.py',
    nodes: [
      {
        id: 'file:agent/tools/_result.py',
        type: 'file',
        name: '_result.py',
        filePath: 'agent/tools/_result.py',
        summary: 'Define el tipo de retorno estructurado ToolResult, la enumeración Status y el context manager Timer para estandarizar las respuestas de todas las herramientas del agente.',
        tags: ['resultado-estructurado', 'dataclass', 'timer', 'tools-agente'],
        complexity: 'moderate',
        languageNotes: 'Implementa compatibilidad hacia atrás con Strands SDK mediante __str__ y constructores de clase ok, warn y error.'
      },
      {
        id: 'class:agent/tools/_result.py:Status',
        type: 'class',
        name: 'Status',
        filePath: 'agent/tools/_result.py',
        lineRange: [19, 23],
        summary: 'Enumeración de estado semántico para resultados de herramientas (ok, warning y error).',
        tags: ['enum', 'estado', 'tools-agente'],
        complexity: 'simple'
      },
      {
        id: 'class:agent/tools/_result.py:ToolResult',
        type: 'class',
        name: 'ToolResult',
        filePath: 'agent/tools/_result.py',
        lineRange: [27, 124],
        summary: 'Dataclass que encapsula éxito, mensaje formateado, estado, datos estructurados, sugerencias y duración de ejecución con atajos ok, warn, error y serialización to_dict.',
        tags: ['dataclass', 'resultado-estructurado', 'serializacion'],
        complexity: 'moderate'
      },
      {
        id: 'class:agent/tools/_result.py:Timer',
        type: 'class',
        name: 'Timer',
        filePath: 'agent/tools/_result.py',
        lineRange: [127, 149],
        summary: 'Context manager basado en time.perf_counter para medir la duración en milisegundos de operaciones de herramientas.',
        tags: ['context-manager', 'cronometro', 'telemetria'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:Status', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:Status', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:ToolResult', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:ToolResult', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:Timer', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/_result.py', target: 'class:agent/tools/_result.py:Timer', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'class:agent/tools/_result.py:ToolResult', target: 'class:agent/tools/_result.py:Status', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'agent/tools/project_index.py',
    nodes: [
      {
        id: 'file:agent/tools/project_index.py',
        type: 'file',
        name: 'project_index.py',
        filePath: 'agent/tools/project_index.py',
        summary: 'Generador del índice estructural JSON del ecosistema nas-dotfiles + DebMenux y del mapa legible docs/CODE-MAP.md mediante análisis AST de Python y parsing de scripts Bash.',
        tags: ['indice-proyecto', 'ast-python', 'code-map', 'contratos', 'herramienta-cli'],
        complexity: 'complex',
        languageNotes: 'Combina hashlib, ast y expresiones regulares para inspeccionar paridad de comandos CLI, capacidades, gateways MCP y contratos arquitectónicos.'
      },
      { id: 'function:agent/tools/project_index.py:_relative', type: 'function', name: '_relative', filePath: 'agent/tools/project_index.py', lineRange: [53, 54], summary: 'Convierte una ruta Path en cadena POSIX relativa a la raíz indicada.', tags: ['rutas', 'helper', 'posix'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_iter_repo_files', type: 'function', name: '_iter_repo_files', filePath: 'agent/tools/project_index.py', lineRange: [57, 75], summary: 'Recorre archivos de un repositorio excluyendo directorios ignorados, archivos de entorno y cachés.', tags: ['descubrimiento-archivos', 'recorrido-repo', 'helper'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_classify_path', type: 'function', name: '_classify_path', filePath: 'agent/tools/project_index.py', lineRange: [78, 135], summary: 'Clasifica cada ruta relativa de nas-dotfiles o DebMenux según su rol arquitectónico (CLI, tool, gateway MCP, guía, ficha o hook).', tags: ['clasificacion', 'arquitectura', 'inventario'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_sha256', type: 'function', name: '_sha256', filePath: 'agent/tools/project_index.py', lineRange: [138, 146], summary: 'Calcula el hash SHA-256 en lectura por bloques de un archivo del repositorio.', tags: ['hashing', 'sha256', 'integridad'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_read_text', type: 'function', name: '_read_text', filePath: 'agent/tools/project_index.py', lineRange: [149, 153], summary: 'Lee el contenido UTF-8 de un archivo devolviendo cadena vacía si ocurre un OSError.', tags: ['lectura-archivo', 'helper', 'utf8'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_file_records', type: 'function', name: '_file_records', filePath: 'agent/tools/project_index.py', lineRange: [156, 170], summary: 'Construye los registros indexados de todos los archivos de nas-dotfiles y DebMenux con tamaño, tipo y hash SHA-256.', tags: ['inventario-archivos', 'metadatos', 'indice-proyecto'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_extract_bash_commands', type: 'function', name: '_extract_bash_commands', filePath: 'agent/tools/project_index.py', lineRange: [178, 180], summary: 'Extrae los subcomandos declarados en las sentencias case de docker/cli/svc.sh.', tags: ['parsing-bash', 'cli-svc', 'paridad'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_extract_python_commands', type: 'function', name: '_extract_python_commands', filePath: 'agent/tools/project_index.py', lineRange: [183, 220], summary: 'Analiza el AST de svc_py/app.py para extraer los comandos registrados mediante decoradores de Typer.', tags: ['ast-python', 'svc-py', 'paridad'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_extract_completion_commands', type: 'function', name: '_extract_completion_commands', filePath: 'agent/tools/project_index.py', lineRange: [223, 232], summary: 'Extrae los comandos globales y de servicio definidos en el script de autocompletado shell/lib/docker.sh.', tags: ['parsing-bash', 'autocompletado', 'paridad'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_extract_prompt_commands', type: 'function', name: '_extract_prompt_commands', filePath: 'agent/tools/project_index.py', lineRange: [235, 239], summary: 'Detecta los comandos svc documentados dentro del prompt del sistema en agent/nas_agent.py.', tags: ['prompt-agente', 'paridad', 'parsing'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_extract_registered_tools', type: 'function', name: '_extract_registered_tools', filePath: 'agent/tools/project_index.py', lineRange: [242, 262], summary: 'Inspecciona el AST de agent/tools/__init__.py para listar las herramientas registradas en ALL_TOOLS.', tags: ['ast-python', 'tools-agente', 'inventario'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_extract_capabilities', type: 'function', name: '_extract_capabilities', filePath: 'agent/tools/project_index.py', lineRange: [265, 321], summary: 'Recopila las operaciones declaradas en los manifests JSON de agent/capabilities/.', tags: ['capacidades', 'manifests-json', 'inventario'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_extract_mcp_gateways', type: 'function', name: '_extract_mcp_gateways', filePath: 'agent/tools/project_index.py', lineRange: [324, 452], summary: 'Inspecciona mediante AST y manifests los gateways MCP (lobehub_mcp.py y nas_mcp_gateway) validando coherencia entre herramientas y operaciones.', tags: ['gateway-mcp', 'ast-python', 'validacion'], complexity: 'complex' },
      { id: 'function:agent/tools/project_index.py:_extract_service_ids', type: 'function', name: '_extract_service_ids', filePath: 'agent/tools/project_index.py', lineRange: [455, 517], summary: 'Consolida los servicios conocidos cruzando fichas, compose de catálogo, guías y el registro services.json de DebMenux.', tags: ['catalogo-servicios', 'debmenux', 'inventario'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_load_contracts', type: 'function', name: '_load_contracts', filePath: 'agent/tools/project_index.py', lineRange: [525, 529], summary: 'Carga el archivo agent/architecture/contracts.json con los contratos de conexión arquitectónica.', tags: ['contratos', 'arquitectura', 'json'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_resolve_contract_path', type: 'function', name: '_resolve_contract_path', filePath: 'agent/tools/project_index.py', lineRange: [532, 535], summary: 'Resuelve rutas relativas de contratos tanto dentro de nas-dotfiles como hacia el repositorio hermano DebMenux-.', tags: ['contratos', 'resolucion-rutas', 'helper'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_contract_connections', type: 'function', name: '_contract_connections', filePath: 'agent/tools/project_index.py', lineRange: [538, 562], summary: 'Verifica la existencia de todos los artefactos requeridos por cada contrato de conexión en contracts.json.', tags: ['contratos', 'validacion-arquitectura', 'conexiones'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_cli_index', type: 'function', name: '_cli_index', filePath: 'agent/tools/project_index.py', lineRange: [565, 607], summary: 'Calcula la matriz de paridad de comandos entre svc.sh, svc_py, autocompletado Bash, prompt del agente y ALL_TOOLS.', tags: ['paridad-cli', 'svc', 'indice-proyecto'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:build_index', type: 'function', name: 'build_index', filePath: 'agent/tools/project_index.py', lineRange: [610, 647], summary: 'Construye el índice estructural completo combinando archivos, CLI, servicios, capacidades, gateways MCP y contratos.', tags: ['indice-proyecto', 'orquestacion', 'json'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:write_index', type: 'function', name: 'write_index', filePath: 'agent/tools/project_index.py', lineRange: [650, 654], summary: 'Serializa y escribe el índice estructural JSON en disco creando los directorios padres si es necesario.', tags: ['escritura-json', 'indice-proyecto', 'persistencia'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_is_code_file', type: 'function', name: '_cm_is_code_file', filePath: 'agent/tools/project_index.py', lineRange: [676, 684], summary: 'Determina si un archivo pertenece al código ejecutable (.py, .sh o script con shebang) para incluirlo en CODE-MAP.', tags: ['code-map', 'filtro-archivos', 'helper'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_iter_files', type: 'function', name: '_cm_iter_files', filePath: 'agent/tools/project_index.py', lineRange: [687, 704], summary: 'Lista ordenadamente los archivos de código de los directorios principales y scripts raíz para generar CODE-MAP.', tags: ['code-map', 'descubrimiento-archivos'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_py_purpose', type: 'function', name: '_cm_py_purpose', filePath: 'agent/tools/project_index.py', lineRange: [707, 716], summary: 'Extrae la primera línea descriptiva del docstring de un módulo Python para CODE-MAP.', tags: ['code-map', 'ast-python', 'docstring'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_py_symbols', type: 'function', name: '_cm_py_symbols', filePath: 'agent/tools/project_index.py', lineRange: [719, 740], summary: 'Extrae clases con sus métodos públicos y funciones de nivel superior (marcando decoradores @tool) de un módulo Python.', tags: ['code-map', 'ast-python', 'simbolos'], complexity: 'moderate' },
      { id: 'function:agent/tools/project_index.py:_cm_py_imports', type: 'function', name: '_cm_py_imports', filePath: 'agent/tools/project_index.py', lineRange: [743, 748], summary: 'Identifica importaciones internas hacia los paquetes agent y svc_py mediante recorrido del AST.', tags: ['code-map', 'ast-python', 'dependencias'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_sh_purpose', type: 'function', name: '_cm_sh_purpose', filePath: 'agent/tools/project_index.py', lineRange: [751, 769], summary: 'Extrae el primer comentario descriptivo tras el shebang de un script Bash omitiendo separadores decorativos.', tags: ['code-map', 'parsing-bash', 'comentarios'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_sh_symbols', type: 'function', name: '_cm_sh_symbols', filePath: 'agent/tools/project_index.py', lineRange: [772, 781], summary: 'Lista los nombres de funciones definidas en un script Bash evitando duplicados.', tags: ['code-map', 'parsing-bash', 'simbolos'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_sh_sources', type: 'function', name: '_cm_sh_sources', filePath: 'agent/tools/project_index.py', lineRange: [784, 791], summary: 'Detecta las rutas cargadas con source o punto en scripts Bash normalizando variables de entorno.', tags: ['code-map', 'parsing-bash', 'dependencias'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_analyze', type: 'function', name: '_cm_analyze', filePath: 'agent/tools/project_index.py', lineRange: [794, 802], summary: 'Analiza un archivo Python o Bash devolviendo su propósito, símbolos y conexiones internas.', tags: ['code-map', 'analisis-estatico'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_module_name', type: 'function', name: '_cm_module_name', filePath: 'agent/tools/project_index.py', lineRange: [805, 812], summary: 'Convierte la ruta de un archivo Python al nombre de módulo importable para construir el grafo inverso de uso.', tags: ['code-map', 'modulos-python', 'grafo-inverso'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:_cm_fmt_syms', type: 'function', name: '_cm_fmt_syms', filePath: 'agent/tools/project_index.py', lineRange: [815, 820], summary: 'Formatea la lista de símbolos truncando al máximo configurado para las tablas Markdown de CODE-MAP.', tags: ['code-map', 'formato-markdown', 'helper'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:build_code_map', type: 'function', name: 'build_code_map', filePath: 'agent/tools/project_index.py', lineRange: [823, 893], summary: 'Genera el documento Markdown docs/CODE-MAP.md agrupado por directorio con propósito, símbolos, conexiones y grafo inverso de uso.', tags: ['code-map', 'generacion-docs', 'grafo-inverso'], complexity: 'complex' },
      { id: 'function:agent/tools/project_index.py:write_code_map', type: 'function', name: 'write_code_map', filePath: 'agent/tools/project_index.py', lineRange: [896, 899], summary: 'Escribe el contenido generado por build_code_map en docs/CODE-MAP.md.', tags: ['code-map', 'escritura-archivo', 'documentacion'], complexity: 'simple' },
      { id: 'function:agent/tools/project_index.py:main', type: 'function', name: 'main', filePath: 'agent/tools/project_index.py', lineRange: [902, 938], summary: 'CLI principal que soporta --code-map, --check, --json y --output para generar o validar los índices del proyecto.', tags: ['entrypoint', 'cli', 'indice-proyecto'], complexity: 'moderate' }
    ],
    edges: [
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_relative', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_relative', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_iter_repo_files', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_iter_repo_files', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_classify_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_classify_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_sha256', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_sha256', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_read_text', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_read_text', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_file_records', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_file_records', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_bash_commands', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_bash_commands', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_python_commands', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_python_commands', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_completion_commands', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_completion_commands', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_prompt_commands', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_prompt_commands', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_registered_tools', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_registered_tools', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_capabilities', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_capabilities', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_mcp_gateways', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_mcp_gateways', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_service_ids', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_extract_service_ids', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_load_contracts', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_load_contracts', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_resolve_contract_path', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_resolve_contract_path', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_contract_connections', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_contract_connections', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cli_index', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cli_index', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:build_index', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:build_index', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:write_index', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:write_index', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_is_code_file', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_is_code_file', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_iter_files', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_iter_files', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_purpose', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_purpose', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_symbols', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_symbols', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_imports', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_py_imports', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_purpose', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_purpose', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_symbols', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_symbols', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_sources', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_sh_sources', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_analyze', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_analyze', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_module_name', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_module_name', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_fmt_syms', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:_cm_fmt_syms', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:build_code_map', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:build_code_map', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:write_code_map', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:write_code_map', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:main', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:agent/tools/project_index.py', target: 'function:agent/tools/project_index.py:main', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_iter_repo_files', target: 'function:agent/tools/project_index.py:_relative', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_file_records', target: 'function:agent/tools/project_index.py:_iter_repo_files', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_file_records', target: 'function:agent/tools/project_index.py:_classify_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_file_records', target: 'function:agent/tools/project_index.py:_sha256', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_bash_commands', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_python_commands', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_completion_commands', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_prompt_commands', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_registered_tools', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_capabilities', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_capabilities', target: 'function:agent/tools/project_index.py:_relative', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_mcp_gateways', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_mcp_gateways', target: 'function:agent/tools/project_index.py:_relative', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_service_ids', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_extract_service_ids', target: 'function:agent/tools/project_index.py:_relative', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_contract_connections', target: 'function:agent/tools/project_index.py:_resolve_contract_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_contract_connections', target: 'function:agent/tools/project_index.py:_classify_path', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cli_index', target: 'function:agent/tools/project_index.py:_extract_bash_commands', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cli_index', target: 'function:agent/tools/project_index.py:_extract_python_commands', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cli_index', target: 'function:agent/tools/project_index.py:_extract_completion_commands', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cli_index', target: 'function:agent/tools/project_index.py:_extract_prompt_commands', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cli_index', target: 'function:agent/tools/project_index.py:_extract_registered_tools', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_load_contracts', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_file_records', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_extract_service_ids', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_extract_capabilities', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_extract_mcp_gateways', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_cli_index', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_index', target: 'function:agent/tools/project_index.py:_contract_connections', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_iter_files', target: 'function:agent/tools/project_index.py:_cm_is_code_file', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_read_text', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_py_purpose', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_py_symbols', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_py_imports', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_sh_purpose', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_sh_symbols', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:_cm_analyze', target: 'function:agent/tools/project_index.py:_cm_sh_sources', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_code_map', target: 'function:agent/tools/project_index.py:_cm_iter_files', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_code_map', target: 'function:agent/tools/project_index.py:_cm_analyze', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_code_map', target: 'function:agent/tools/project_index.py:_cm_module_name', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:build_code_map', target: 'function:agent/tools/project_index.py:_cm_fmt_syms', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:write_code_map', target: 'function:agent/tools/project_index.py:build_code_map', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:main', target: 'function:agent/tools/project_index.py:write_code_map', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:main', target: 'function:agent/tools/project_index.py:build_index', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'function:agent/tools/project_index.py:main', target: 'function:agent/tools/project_index.py:write_index', type: 'calls', direction: 'forward', weight: 0.8 },
      { source: 'file:agent/tools/project_index.py', target: 'config:agent/architecture/contracts.json', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'file:docker/cli/svc.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'file:svc_py/app.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'file:shell/lib/docker.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'file:agent/nas_agent.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'file:agent/tools/__init__.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:agent/tools/project_index.py', target: 'document:docs/CODE-MAP.md', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'docker-nas/SKILL.md',
    nodes: [
      {
        id: 'document:docker-nas/SKILL.md',
        type: 'document',
        name: 'SKILL.md',
        filePath: 'docker-nas/SKILL.md',
        summary: 'Definición principal de la skill docker-nas, que establece reglas estrictas del entorno NAS, el protocolo para instalar servicios Docker, comandos esenciales y el índice de guías y referencias.',
        tags: ['skill-ia', 'docker-nas', 'protocolo-servicios', 'reglas-entorno'],
        complexity: 'complex',
        languageNotes: 'Markdown con frontmatter YAML de activación para agentes IA y tablas de referencia cruzada hacia guías de servicios.'
      }
    ],
    edges: [
      { source: 'document:docker-nas/SKILL.md', target: 'document:docker-nas/references/nas-context.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'document:docker-nas/references/entorno.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'document:docker-nas/references/svc.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'document:docker-nas/references/agent.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'file:docker/cli/svc.sh', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'file:docker/cli/lib/notifications.sh', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:docker-nas/SKILL.md', target: 'file:agent/plugins/notification_plugin.py', type: 'documents', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'docker/cli/svc.sh',
    nodes: [
      {
        id: 'file:docker/cli/svc.sh',
        type: 'file',
        name: 'svc.sh',
        filePath: 'docker/cli/svc.sh',
        summary: 'Entrypoint principal del CLI Bash svc para administrar servicios Docker del NAS; carga las librerías de docker/cli/lib/, despacha subcomandos globales y por servicio, y aplica --env-file global y local.',
        tags: ['cli-bash', 'svc', 'docker-compose', 'despachador'],
        complexity: 'moderate',
        languageNotes: 'Script Bash con set -e que delega comandos avanzados (diff, capabilities, scan, code-map) a scripts Python en agent/tools/.'
      }
    ],
    edges: [
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/discovery.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/docker.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/health.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/backup.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/extras.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/menu.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/lobehub.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/help.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:docker/cli/lib/catalog-sync.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:agent/tools/compare_tools.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:agent/tools/capabilities.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:agent/tools/project_scanner.py', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:docker/cli/svc.sh', target: 'file:agent/tools/project_index.py', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'docs/services/vscode-guide.md',
    nodes: [
      {
        id: 'document:docs/services/vscode-guide.md',
        type: 'document',
        name: 'vscode-guide.md',
        filePath: 'docs/services/vscode-guide.md',
        summary: 'Guía operativa completa para desplegar y mantener VS Code Server (code-server) en Docker sin privilegios de root, cubriendo permisos ACL sobre Home Assistant, verificación, backup y troubleshooting.',
        tags: ['guia-servicio', 'vscode', 'code-server', 'docker', 'seguridad-acl'],
        complexity: 'moderate',
        languageNotes: 'Documentación operativa en Markdown con comandos verificables para NAS Debian y referencias a docker-entorno y homeassistant-guide.'
      }
    ],
    edges: [
      { source: 'document:docs/services/vscode-guide.md', target: 'service:agent/catalog/services/vscode/compose.yml', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:docs/services/vscode-guide.md', target: 'document:agent/catalog/services/vscode/ficha.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docs/services/vscode-guide.md', target: 'document:docs/docker-entorno.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:docs/services/vscode-guide.md', target: 'document:docs/services/homeassistant-guide.md', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'setup',
    nodes: [
      {
        id: 'file:setup',
        type: 'file',
        name: 'setup',
        filePath: 'setup',
        summary: 'Script ejecutable Bash que actúa como punto de entrada universal de instalación de nas-dotfiles; detecta Python y las librerías Rich/InquirerPy para lanzar ui/setup.py o recurrir a install.sh.',
        tags: ['instalador', 'entrypoint', 'tui-python', 'fallback-bash'],
        complexity: 'simple',
        languageNotes: 'Script Bash sin extensión que intenta instalar dependencias vía pip o venv temporal antes de delegar en install.sh.'
      }
    ],
    edges: [
      { source: 'file:setup', target: 'file:ui/setup.py', type: 'triggers', direction: 'forward', weight: 0.6 },
      { source: 'file:setup', target: 'file:install.sh', type: 'triggers', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'shell/init.sh',
    nodes: [
      {
        id: 'file:shell/init.sh',
        type: 'file',
        name: 'init.sh',
        filePath: 'shell/init.sh',
        summary: 'Cargador único del framework de shell para nas-dotfiles; valida NAS_DOTFILES, carga user.conf y $DOCKER_BASE/.env, define path_add, svc y agent, e importa los módulos de shell/lib/.',
        tags: ['shell-framework', 'inicializacion', 'bash', 'cli-dual'],
        complexity: 'moderate',
        languageNotes: 'Script Bash pensado para ser incluido con source desde ~/.bashrc con guardia contra recarga múltiple.'
      },
      {
        id: 'function:shell/init.sh:path_add',
        type: 'function',
        name: 'path_add',
        filePath: 'shell/init.sh',
        lineRange: [39, 44],
        summary: 'Antepone un directorio a la variable PATH únicamente si no se encuentra ya presente y se exporta con export -f.',
        tags: ['path', 'funcion-shell', 'bash'],
        complexity: 'simple'
      }
    ],
    edges: [
      { source: 'file:shell/init.sh', target: 'function:shell/init.sh:path_add', type: 'contains', direction: 'forward', weight: 1.0 },
      { source: 'file:shell/init.sh', target: 'function:shell/init.sh:path_add', type: 'exports', direction: 'forward', weight: 0.8 },
      { source: 'file:shell/init.sh', target: 'file:docker/cli/svc.sh', type: 'triggers', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:svc_py/__main__.py', type: 'triggers', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:agent/nas_agent.py', type: 'triggers', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/aliases.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/nav.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/docker.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/system.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/instal.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/pipins.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/git.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/completions.sh', type: 'depends_on', direction: 'forward', weight: 0.6 },
      { source: 'file:shell/init.sh', target: 'file:shell/lib/prompt.sh', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'shell/scripts/layers.conf.example',
    nodes: [
      {
        id: 'file:shell/scripts/layers.conf.example',
        type: 'file',
        name: 'layers.conf.example',
        filePath: 'shell/scripts/layers.conf.example',
        summary: 'Plantilla de ejemplo para configurar el arranque escalonado por capas de servicios Docker mediante boot-order.sh, ordenando DataSQL, consumidores, IoT, archivos y dashboard.',
        tags: ['plantilla-config', 'arranque-escalonado', 'capas-servicios', 'boot-order'],
        complexity: 'simple',
        languageNotes: 'Archivo de texto plano con comentarios explicativos e identificadores de proyecto por capa separados por líneas en blanco.'
      }
    ],
    edges: []
  },
  {
    path: 'skill-portable/nas-tools-index/README.md',
    nodes: [
      {
        id: 'document:skill-portable/nas-tools-index/README.md',
        type: 'document',
        name: 'README.md',
        filePath: 'skill-portable/nas-tools-index/README.md',
        summary: 'Instrucciones de empaquetado, carga y mantenimiento del espejo portable de la skill nas-tools-index sincronizada manualmente desde docs/tools-index.md.',
        tags: ['skill-portable', 'documentacion', 'empaquetado-zip', 'espejo'],
        complexity: 'simple',
        languageNotes: 'Guía breve en Markdown con comandos zip y Python shutil para distribuir la skill a otros clientes LLM.'
      }
    ],
    edges: [
      { source: 'document:skill-portable/nas-tools-index/README.md', target: 'document:skill-portable/nas-tools-index/SKILL.md', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:skill-portable/nas-tools-index/README.md', target: 'file:skill-portable/nas-tools-index/scripts/tool-lookup.sh', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:skill-portable/nas-tools-index/README.md', target: 'document:docs/tools-index.md', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'skill-portable/nas-tools-index/SKILL.md',
    nodes: [
      {
        id: 'document:skill-portable/nas-tools-index/SKILL.md',
        type: 'document',
        name: 'SKILL.md',
        filePath: 'skill-portable/nas-tools-index/SKILL.md',
        summary: 'Copia portable y autocontenida del índice de herramientas de nas-dotfiles (aliases, funciones de navegación, comandos svc, skills y tools del agente) para uso de LLMs sin acceso al repositorio.',
        tags: ['skill-portable', 'indice-herramientas', 'aliases-shell', 'svc'],
        complexity: 'moderate',
        languageNotes: 'Markdown con frontmatter YAML y tablas estructuradas consultables directamente o mediante tool-lookup.sh.'
      }
    ],
    edges: [
      { source: 'document:skill-portable/nas-tools-index/SKILL.md', target: 'document:docs/tools-index.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:skill-portable/nas-tools-index/SKILL.md', target: 'document:docker-nas/references/entorno.md', type: 'related', direction: 'forward', weight: 0.5 },
      { source: 'document:skill-portable/nas-tools-index/SKILL.md', target: 'file:skill-portable/nas-tools-index/scripts/tool-lookup.sh', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'skill-portable/nas-tools-index/scripts/tool-lookup.sh',
    nodes: [
      {
        id: 'file:skill-portable/nas-tools-index/scripts/tool-lookup.sh',
        type: 'file',
        name: 'tool-lookup.sh',
        filePath: 'skill-portable/nas-tools-index/scripts/tool-lookup.sh',
        summary: 'Script auxiliar Bash que consulta las tablas de skill-portable/nas-tools-index/SKILL.md mediante grep para localizar una herramienta por nombre o listar todas las documentadas.',
        tags: ['script-auxiliar', 'busqueda-grep', 'skill-portable', 'bash'],
        complexity: 'simple',
        languageNotes: 'Script Bash con set -euo pipefail que resuelve la ruta relativa de SKILL.md respecto a BASH_SOURCE.'
      }
    ],
    edges: [
      { source: 'file:skill-portable/nas-tools-index/scripts/tool-lookup.sh', target: 'document:skill-portable/nas-tools-index/SKILL.md', type: 'depends_on', direction: 'forward', weight: 0.6 }
    ]
  },
  {
    path: 'svc_py/README.md',
    nodes: [
      {
        id: 'document:svc_py/README.md',
        type: 'document',
        name: 'README.md',
        filePath: 'svc_py/README.md',
        summary: 'Documentación del CLI Python svc_py como alternativa con UI enriquecida (Rich e InquirerPy) al CLI Bash svc.sh, detallando instalación, activación con NAS_CLI=python y tabla comparativa.',
        tags: ['documentacion', 'svc-py', 'cli-python', 'rich', 'inquirerpy'],
        complexity: 'simple',
        languageNotes: 'Documento Markdown descriptivo para usuarios y desarrolladores del CLI dual.'
      }
    ],
    edges: [
      { source: 'document:svc_py/README.md', target: 'file:svc_py/__init__.py', type: 'documents', direction: 'forward', weight: 0.5 },
      { source: 'document:svc_py/README.md', target: 'file:docker/cli/svc.sh', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'svc_py/__init__.py',
    nodes: [
      {
        id: 'file:svc_py/__init__.py',
        type: 'file',
        name: '__init__.py',
        filePath: 'svc_py/__init__.py',
        summary: 'Archivo de inicialización del paquete svc_py, que documenta el propósito y uso básico de la interfaz Python alternativa a svc.sh para gestionar servicios Docker del NAS.',
        tags: ['paquete-python', 'svc-py', 'cli-docker'],
        complexity: 'simple',
        languageNotes: 'Contiene únicamente el docstring introductorio del paquete.'
      }
    ],
    edges: [
      { source: 'file:svc_py/__init__.py', target: 'file:svc_py/app.py', type: 'related', direction: 'forward', weight: 0.5 }
    ]
  },
  {
    path: 'svc_py/core/__init__.py',
    nodes: [
      {
        id: 'file:svc_py/core/__init__.py',
        type: 'file',
        name: '__init__.py',
        filePath: 'svc_py/core/__init__.py',
        summary: 'Archivo marcador del subpaquete svc_py.core, que agrupa los módulos de descubrimiento de servicios e interacción con Docker.',
        tags: ['paquete-python', 'svc-py', 'core-docker'],
        complexity: 'simple',
        languageNotes: 'Contiene un docstring de una sola línea sin símbolos definidos.'
      }
    ],
    edges: []
  }
];

// Ordenar alfabéticamente por path (ya está ordenado, pero aseguramos)
files.sort((a, b) => a.path.localeCompare(b.path));

const totalNodes = files.reduce((acc, f) => acc + f.nodes.length, 0);
const totalEdges = files.reduce((acc, f) => acc + f.edges.length, 0);
const minParts = Math.ceil(Math.max(totalNodes / 60, totalEdges / 120));

console.log({ totalNodes, totalEdges, minParts });

// Chunking files alphabetically keeping each part <= 60 nodes and <= 120 edges
const parts = [];
let curNodes = [];
let curEdges = [];
for (const f of files) {
  if (
    curNodes.length > 0 &&
    (curNodes.length + f.nodes.length > 60 || curEdges.length + f.edges.length > 120)
  ) {
    parts.push({ nodes: curNodes, edges: curEdges });
    curNodes = [];
    curEdges = [];
  }
  curNodes.push(...f.nodes);
  curEdges.push(...f.edges);
}
if (curNodes.length > 0 || curEdges.length > 0) {
  parts.push({ nodes: curNodes, edges: curEdges });
}

console.log('Generated parts:', parts.length);
for (let i = 0; i < parts.length; i++) {
  const p = parts[i];
  const partName = parts.length === 1 ? 'batch-38.json' : `batch-38-part-${i + 1}.json`;
  const outPath = path.join(OUT_DIR, partName);
  // Check no self-loops & no duplicate node IDs
  const ids = new Set();
  for (const n of p.nodes) {
    if (ids.has(n.id)) throw new Error('Duplicate node id: ' + n.id);
    ids.add(n.id);
  }
  for (const e of p.edges) {
    if (e.source === e.target) throw new Error('Self-loop: ' + e.source);
    if (!ids.has(e.source)) throw new Error('Edge source not in part: ' + e.source);
  }
  fs.writeFileSync(outPath, JSON.stringify({ nodes: p.nodes, edges: p.edges }, null, 2) + '\n', 'utf8');
  console.log(partName, 'nodes:', p.nodes.length, 'edges:', p.edges.length);
}
