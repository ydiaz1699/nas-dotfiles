import fs from 'node:fs';
import path from 'node:path';

const UA_DIR = 'C:/Users/Alex/Desktop/1-Github/nas-dotfiles/.ua';
const extract = JSON.parse(fs.readFileSync(`${UA_DIR}/tmp/ua-file-extract-results-1.json`, 'utf8'));
const meta = JSON.parse(fs.readFileSync(`${UA_DIR}/tmp/ua-batch-1-meta.json`, 'utf8'));

const FILE_SPECS = {
  'svc_py/__main__.py': {
    summary: 'Punto de entrada para ejecutar el CLI con python -m svc_py; configura Rich traceback con variables locales y arranca la aplicación Typer principal.',
    tags: ['entry-point', 'cli', 'bootstrap'],
    complexity: 'simple',
    functions: {}
  },
  'svc_py/app.py': {
    summary: 'Aplicación principal Typer del CLI svc que registra todos los subcomandos modulares y define comandos globales y wrappers passthrough hacia docker compose y svc.sh.',
    tags: ['cli', 'entry-point', 'typer', 'docker-compose', 'orquestacion'],
    complexity: 'complex',
    languageNotes: 'Usa decoradores @app.command() de Typer y registro imperativo de funciones importadas desde submódulos para centralizar la interfaz CLI.',
    functions: {
      snapshot: {
        summary: 'Delega en svc.sh el guardado de un snapshot liviano de configuración de un servicio.',
        tags: ['cli-command', 'snapshot', 'passthrough'],
        complexity: 'simple'
      },
      capabilities: {
        summary: 'Reenvía al CLI Bash la consulta de capacidades del proyecto desde manifests e índice estructural.',
        tags: ['cli-command', 'capacidades', 'passthrough'],
        complexity: 'simple'
      },
      lobehub: {
        summary: 'Ejecuta operaciones seguras sobre LobeHub delegando en svc.sh con soporte para confirmación.',
        tags: ['cli-command', 'lobehub', 'passthrough'],
        complexity: 'simple'
      },
      no_boot: {
        summary: 'Excluye un servicio del arranque escalonado o lista los excluidos delegando en svc.sh.',
        tags: ['cli-command', 'arranque', 'passthrough'],
        complexity: 'simple'
      },
      boot_enable: {
        summary: 'Reactiva un servicio en el arranque escalonado eliminando su marcador .no-boot vía svc.sh.',
        tags: ['cli-command', 'arranque', 'passthrough'],
        complexity: 'simple'
      },
      boot_status: {
        summary: 'Consulta el estado del arranque escalonado del sistema delegando en svc.sh.',
        tags: ['cli-command', 'arranque', 'estado'],
        complexity: 'simple'
      },
      lista: {
        summary: 'Lista todos los servicios Docker detectados mostrando su estado activo o detenido en una tabla Rich.',
        tags: ['cli-command', 'listado', 'rich', 'estado'],
        complexity: 'moderate'
      },
      up: {
        summary: 'Crea e inicia en segundo plano los contenedores del servicio indicado mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      down: {
        summary: 'Detiene y elimina los contenedores del servicio indicado mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      start: {
        summary: 'Inicia un servicio previamente detenido mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      stop: {
        summary: 'Detiene los contenedores en ejecución de un servicio mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      restart: {
        summary: 'Reinicia los contenedores de un servicio mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      kill_svc: {
        summary: 'Fuerza la parada inmediata de los contenedores de un servicio mediante _docker_action.',
        tags: ['cli-command', 'docker-compose', 'ciclo-vida'],
        complexity: 'simple'
      },
      update: {
        summary: 'Descarga nuevas imágenes y recrea los contenedores del servicio eliminando huérfanos.',
        tags: ['cli-command', 'docker-compose', 'actualizacion'],
        complexity: 'simple'
      },
      recreate: {
        summary: 'Recrea los contenedores del servicio con la imagen local sin ejecutar pull.',
        tags: ['cli-command', 'docker-compose', 'recreacion'],
        complexity: 'simple'
      },
      logs: {
        summary: 'Muestra los logs en vivo del servicio con streaming interactivo y límite de líneas configurable.',
        tags: ['cli-command', 'logs', 'streaming'],
        complexity: 'simple'
      },
      ps_cmd: {
        summary: 'Lista el estado de los contenedores de un servicio delegando en compose_passthrough.',
        tags: ['cli-command', 'contenedores', 'estado'],
        complexity: 'simple'
      },
      stats: {
        summary: 'Muestra el uso de CPU y memoria en tiempo real de los contenedores del servicio.',
        tags: ['cli-command', 'metricas', 'monitoreo'],
        complexity: 'simple'
      },
      top: {
        summary: 'Muestra los procesos activos dentro de los contenedores del servicio.',
        tags: ['cli-command', 'procesos', 'inspeccion'],
        complexity: 'simple'
      },
      exec_cmd: {
        summary: 'Ejecuta un comando arbitrario o abre una shell sh dentro del contenedor del servicio.',
        tags: ['cli-command', 'shell', 'ejecucion'],
        complexity: 'simple'
      },
      build: {
        summary: 'Construye o reconstruye la imagen Docker del servicio mediante _docker_action.',
        tags: ['cli-command', 'build', 'docker-compose'],
        complexity: 'simple'
      },
      pull: {
        summary: 'Descarga la imagen Docker configurada para el servicio mediante _docker_action.',
        tags: ['cli-command', 'imagenes', 'docker-compose'],
        complexity: 'simple'
      },
      images: {
        summary: 'Lista las imágenes Docker asociadas a un servicio mediante compose_passthrough.',
        tags: ['cli-command', 'imagenes', 'inspeccion'],
        complexity: 'simple'
      },
      rm_cmd: {
        summary: 'Elimina contenedores detenidos de un servicio mediante _docker_action.',
        tags: ['cli-command', 'limpieza', 'docker-compose'],
        complexity: 'simple'
      },
      config: {
        summary: 'Imprime la configuración docker compose resuelta del servicio.',
        tags: ['cli-command', 'configuracion', 'docker-compose'],
        complexity: 'simple'
      },
      events: {
        summary: 'Transmite en tiempo real los eventos de Docker del servicio.',
        tags: ['cli-command', 'eventos', 'monitoreo'],
        complexity: 'simple'
      },
      volumes: {
        summary: 'Lista los volúmenes declarados en la configuración del servicio.',
        tags: ['cli-command', 'volumenes', 'almacenamiento'],
        complexity: 'simple'
      },
      _get_compose_or_exit: {
        summary: 'Resuelve el archivo compose de un servicio o finaliza el CLI mostrando la lista disponible.',
        tags: ['helper', 'validacion', 'docker-compose'],
        complexity: 'simple'
      },
      _docker_action: {
        summary: 'Helper compartido que valida el compose file, imprime confirmación y ejecuta una acción docker compose.',
        tags: ['helper', 'docker-compose', 'ejecucion'],
        complexity: 'simple'
      }
    }
  },
  'svc_py/commands/__init__.py': {
    summary: 'Inicializador del paquete svc_py.commands que agrupa los módulos de subcomandos del CLI.',
    tags: ['paquete', 'inicializador', 'cli'],
    complexity: 'simple',
    functions: {}
  },
  'svc_py/commands/backup.py': {
    summary: 'Implementa los comandos backup y restore para respaldar y restaurar volúmenes Docker y bind mounts con barras de progreso Rich, selector InquirerPy y rotación automática.',
    tags: ['backup', 'restore', 'docker-volumes', 'cli', 'almacenamiento'],
    complexity: 'complex',
    languageNotes: 'Combina contenedores temporales alpine vía Docker CLI para volúmenes nombrados con tar local para bind mounts, y degrada a listado manual si falta InquirerPy.',
    functions: {
      _get_volumes: {
        summary: 'Extrae los nombres de volúmenes declarados en un archivo compose mediante docker compose config --volumes.',
        tags: ['helper', 'volumenes', 'docker-compose'],
        complexity: 'simple'
      },
      _get_bind_mounts: {
        summary: 'Parsea la salida de docker compose config para detectar rutas absolutas montadas como bind mounts.',
        tags: ['helper', 'bind-mounts', 'parsing'],
        complexity: 'moderate'
      },
      _rotate_backups: {
        summary: 'Elimina los archivos .tar.gz más antiguos de un servicio cuando superan el límite BACKUP_KEEP.',
        tags: ['helper', 'rotacion', 'almacenamiento'],
        complexity: 'simple'
      },
      backup: {
        summary: 'Respalda volúmenes nombrados usando un contenedor alpine y bind mounts locales en archivos .tar.gz con progreso visual y rotación.',
        tags: ['cli-command', 'backup', 'docker-volumes', 'rich'],
        complexity: 'complex'
      },
      restore: {
        summary: 'Restaura un backup de volumen o bind mount tras selección interactiva y confirmación, deteniendo y levantando el servicio si aplica.',
        tags: ['cli-command', 'restore', 'inquirerpy', 'docker-volumes'],
        complexity: 'complex'
      }
    }
  },
  'svc_py/commands/catalog.py': {
    summary: 'Implementa el comando catalog-sync con tabla de estado de documentación (--status), regeneración de catalog.json y delegación al script Bash o fallback nativo.',
    tags: ['catalogo', 'documentacion', 'cli', 'sincronizacion', 'rich'],
    complexity: 'complex',
    functions: {
      catalog_sync: {
        summary: 'Punto de entrada del comando catalog-sync que despacha hacia estado, regeneración de índice, script Bash o sincronización nativa.',
        tags: ['cli-command', 'catalogo', 'sincronizacion'],
        complexity: 'moderate'
      },
      _show_status: {
        summary: 'Muestra una tabla Rich con el estado de compose, ficha, guía, script DebMenux y labels Homepage por cada servicio.',
        tags: ['helper', 'estado', 'rich', 'documentacion'],
        complexity: 'moderate'
      },
      _regenerate_index: {
        summary: 'Ejecuta python3 -m agent.catalog._index para reconstruir catalog.json desde las fichas del catálogo.',
        tags: ['helper', 'indice', 'subproceso'],
        complexity: 'simple'
      },
      _run_bash_catalog_sync: {
        summary: 'Invoca la función catalog_sync del script Bash catalog-sync.sh exportando las variables del entorno.',
        tags: ['helper', 'bash', 'subproceso'],
        complexity: 'simple'
      },
      _native_catalog_sync: {
        summary: 'Implementación de respaldo en Python que copia compose.yml faltantes al catálogo, reporta fichas o guías ausentes y regenera el índice.',
        tags: ['helper', 'catalogo', 'fallback'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/codemap.py': {
    summary: 'Implementa el comando code-map que delega en agent/tools/project_index.py --code-map para generar el mapa estructural docs/CODE-MAP.md.',
    tags: ['documentacion', 'indice', 'cli', 'code-map'],
    complexity: 'simple',
    functions: {
      code_map: {
        summary: 'Ejecuta project_index.py --code-map con las variables de entorno del proyecto y propaga su salida y código de retorno.',
        tags: ['cli-command', 'indice', 'subproceso'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/compose.py': {
    summary: 'Provee los comandos create (wizard interactivo para nuevos servicios con compose.yml, .env y README.md) y diff (comparación contra configuración resuelta o catálogo).',
    tags: ['scaffolding', 'docker-compose', 'diff', 'cli', 'wizard'],
    complexity: 'moderate',
    functions: {
      create: {
        summary: 'Crea la estructura inicial de un nuevo servicio (compose.yml, .env, README.md y data/) usando InquirerPy o prompts de Typer.',
        tags: ['cli-command', 'scaffolding', 'wizard', 'docker-compose'],
        complexity: 'moderate'
      },
      diff: {
        summary: 'Compara un compose en disco contra su configuración resuelta resaltando diferencias con Rich Syntax y verificando variables en .env, o delega --all a compare_tools.py.',
        tags: ['cli-command', 'diff', 'validacion', 'docker-compose'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/docker.py': {
    summary: 'Implementa el comando update-all para seleccionar múltiples servicios con InquirerPy y actualizar sus imágenes con barra de progreso Rich.',
    tags: ['docker-compose', 'actualizacion', 'cli', 'progreso', 'interactivo'],
    complexity: 'moderate',
    functions: {
      update_all: {
        summary: 'Permite seleccionar servicios mediante checkbox InquirerPy o confirmación Typer, ejecuta pull y recrea únicamente los que estaban activos.',
        tags: ['cli-command', 'actualizacion', 'multi-select', 'rich'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/health.py': {
    summary: 'Implementa los comandos de observabilidad health, doctor y watch para inspeccionar salud, uptime, reinicios, recursos del NAS y monitoreo en vivo con Rich Live.',
    tags: ['monitoreo', 'salud', 'diagnostico', 'docker', 'cli'],
    complexity: 'complex',
    languageNotes: 'Utiliza rich.live.Live en watch para refrescar la tabla in-place sin limpiar la terminal y combina utilidades Linux (df, free, ss) con inspección Docker.',
    functions: {
      _uptime_str: {
        summary: 'Calcula el tiempo activo legible (m, h, d) a partir de State.StartedAt de un contenedor.',
        tags: ['helper', 'uptime', 'formato'],
        complexity: 'simple'
      },
      _build_health_table: {
        summary: 'Construye la tabla Rich con estado de ejecución, healthcheck, uptime y reinicios de todos los servicios.',
        tags: ['helper', 'rich', 'salud'],
        complexity: 'moderate'
      },
      health: {
        summary: 'Imprime el dashboard puntual de salud de todos los servicios Docker.',
        tags: ['cli-command', 'salud', 'dashboard'],
        complexity: 'simple'
      },
      doctor: {
        summary: 'Ejecuta seis chequeos diagnósticos del NAS: disco, memoria, servicios detenidos o reiniciando, puertos reservados, restart count y almacenamiento Docker.',
        tags: ['cli-command', 'diagnostico', 'sistema', 'auditoria'],
        complexity: 'complex'
      },
      watch: {
        summary: 'Mantiene una tabla Rich Live actualizada periódicamente con estado, CPU, memoria y uptime de cada servicio.',
        tags: ['cli-command', 'monitoreo', 'tiempo-real', 'rich'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/info.py': {
    summary: 'Reúne comandos informativos de inspección (port-map, size, net, depends, env y open) sobre puertos, uso de disco, redes, dependencias, variables de entorno y URLs.',
    tags: ['inspeccion', 'redes', 'puertos', 'variables-entorno', 'cli'],
    complexity: 'complex',
    functions: {
      port_map: {
        summary: 'Recopila puertos expuestos por contenedores activos en una tabla Rich y detecta colisiones entre servicios.',
        tags: ['cli-command', 'puertos', 'conflictos'],
        complexity: 'moderate'
      },
      size: {
        summary: 'Muestra el tamaño en disco del directorio y de la imagen principal de cada servicio mediante du y docker images.',
        tags: ['cli-command', 'almacenamiento', 'disco'],
        complexity: 'moderate'
      },
      net: {
        summary: 'Renderiza un árbol Rich con las redes Docker personalizadas y los contenedores conectados a cada una.',
        tags: ['cli-command', 'redes', 'docker'],
        complexity: 'simple'
      },
      depends: {
        summary: 'Muestra en formato árbol los subservicios y dependencias depends_on declaradas en el compose file de un servicio.',
        tags: ['cli-command', 'dependencias', 'docker-compose'],
        complexity: 'moderate'
      },
      env_cmd: {
        summary: 'Muestra con resaltado INI las variables activas del .env de un servicio o lo abre con el editor configurado.',
        tags: ['cli-command', 'variables-entorno', 'configuracion'],
        complexity: 'moderate'
      },
      open_cmd: {
        summary: 'Detecta el puerto expuesto y la IP del host para imprimir la URL del servicio, copiarla al portapapeles y generar un QR si existe qrencode.',
        tags: ['cli-command', 'url', 'utilidades'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/commands/menu.py': {
    summary: 'Menú TUI interactivo con búsqueda fuzzy mediante InquirerPy, vista previa de contenedores, confirmación de acciones destructivas y ejecución en lote multi-select.',
    tags: ['tui', 'menu', 'interactivo', 'inquirerpy', 'cli'],
    complexity: 'complex',
    languageNotes: 'Emplea importaciones diferidas dentro de _execute_action para reutilizar comandos de backup e info y evitar dependencias circulares.',
    functions: {
      _service_preview: {
        summary: 'Construye un resumen textual con ruta compose, estado, imagen, health, reinicios y puertos de un servicio.',
        tags: ['helper', 'preview', 'tui'],
        complexity: 'moderate'
      },
      _execute_action: {
        summary: 'Despacha acciones individuales o de lote (up, update, logs, backup, depends, etc.) sobre un servicio específico.',
        tags: ['helper', 'despacho', 'acciones'],
        complexity: 'moderate'
      },
      _multi_select_flow: {
        summary: 'Guía la selección múltiple de servicios, la elección de una acción batch, la confirmación destructiva y la ejecución secuencial.',
        tags: ['helper', 'multi-select', 'inquirerpy'],
        complexity: 'moderate'
      },
      menu: {
        summary: 'Bucle principal del menú TUI con búsqueda fuzzy de servicios, panel de preview y selección de acciones individuales o multi-select.',
        tags: ['cli-command', 'tui', 'menu', 'inquirerpy'],
        complexity: 'complex'
      }
    }
  },
  'svc_py/commands/scanner.py': {
    summary: 'Implementa el comando scan del CLI Python invocando el script agent/tools/project_scanner.py con soporte para --verbose y --json.',
    tags: ['auditoria', 'scanner', 'cli', 'inconsistencias'],
    complexity: 'simple',
    functions: {
      scan: {
        summary: 'Configura variables de entorno y ejecuta project_scanner.py como subproceso aislado mostrando su salida en consola.',
        tags: ['cli-command', 'scanner', 'subproceso'],
        complexity: 'moderate'
      }
    }
  },
  'svc_py/config.py': {
    summary: 'Configuración centralizada del CLI Python que lee variables de entorno (DOCKER_BASE, BACKUP_DIR, BACKUP_KEEP, SVC_WATCH_INTERVAL, NAS_DOTFILES) y define los nombres válidos de compose.',
    tags: ['configuracion', 'constantes', 'variables-entorno'],
    complexity: 'simple',
    functions: {}
  },
  'svc_py/core/bash_bridge.py': {
    summary: 'Capa puente entre el CLI Python y el CLI Bash svc.sh (fuente de verdad), exponiendo funciones de ejecución directa, captura, passthrough y verificación de estado.',
    tags: ['bridge', 'bash', 'subprocesos', 'core', 'interoperabilidad'],
    complexity: 'moderate',
    languageNotes: 'Establece NAS_CLI=bash en _build_env() para prevenir recursión infinita cuando el CLI Python delega comandos en svc.sh.',
    functions: {
      _svc_sh_path: {
        summary: 'Localiza svc.sh en NAS_DOTFILES, en el PATH del sistema o en /nas-dotfiles/docker/cli/svc.sh.',
        tags: ['helper', 'rutas', 'validacion'],
        complexity: 'simple'
      },
      _build_env: {
        summary: 'Prepara el diccionario de entorno con DOCKER_BASE, NAS_DOTFILES y NAS_CLI=bash.',
        tags: ['helper', 'entorno', 'configuracion'],
        complexity: 'simple'
      },
      svc: {
        summary: 'Ejecuta un subcomando de svc.sh enviando la salida directamente a la terminal.',
        tags: ['bridge', 'subproceso', 'ejecucion'],
        complexity: 'simple'
      },
      svc_output: {
        summary: 'Ejecuta un subcomando de svc.sh capturando stdout y su código de salida.',
        tags: ['bridge', 'subproceso', 'captura'],
        complexity: 'simple'
      },
      svc_passthrough: {
        summary: 'Ejecuta svc.sh heredando stdin, stdout y stderr para comandos interactivos o en streaming.',
        tags: ['bridge', 'passthrough', 'streaming'],
        complexity: 'simple'
      },
      svc_check: {
        summary: 'Ejecuta un comando de svc.sh silenciosamente y devuelve True si el código de salida es cero.',
        tags: ['bridge', 'verificacion', 'estado'],
        complexity: 'simple'
      },
      svc_list_services: {
        summary: 'Obtiene y parsea la lista de servicios desde svc lista, con fallback a svc_py.core.discovery.svc_list.',
        tags: ['bridge', 'descubrimiento', 'parsing'],
        complexity: 'moderate'
      },
      is_svc_sh_available: {
        summary: 'Comprueba si el script svc.sh es localizable en el sistema.',
        tags: ['helper', 'verificacion', 'disponibilidad'],
        complexity: 'simple'
      }
    }
  },
  'svc_py/core/discovery.py': {
    summary: 'Módulo de descubrimiento de servicios Docker Compose bajo DOCKER_BASE, equivalente en Python a docker/cli/lib/discovery.sh.',
    tags: ['descubrimiento', 'docker-compose', 'core', 'sistema-archivos'],
    complexity: 'moderate',
    functions: {
      svc_list: {
        summary: 'Recorre DOCKER_BASE omitiendo directorios ocultos y backups para devolver los nombres ordenados de servicios con compose file.',
        tags: ['descubrimiento', 'listado', 'servicios'],
        complexity: 'simple'
      },
      svc_compose_file: {
        summary: 'Busca el primer archivo compose válido en el directorio de un servicio según la prioridad de COMPOSE_FILENAMES.',
        tags: ['descubrimiento', 'rutas', 'docker-compose'],
        complexity: 'simple'
      },
      svc_dir: {
        summary: 'Devuelve el Path al directorio de un servicio si existe.',
        tags: ['descubrimiento', 'rutas', 'helper'],
        complexity: 'simple'
      },
      service_exists: {
        summary: 'Indica si un servicio existe verificando que posea un archivo compose válido.',
        tags: ['descubrimiento', 'validacion', 'servicios'],
        complexity: 'simple'
      }
    }
  },
  'svc_py/core/docker.py': {
    summary: 'Abstracción de operaciones Docker que combina el SDK nativo docker-py para inspección rápida, estadísticas y redes con subprocesos docker compose y fallback por CLI.',
    tags: ['docker', 'docker-sdk', 'subprocesos', 'core', 'contenedores'],
    complexity: 'complex',
    languageNotes: 'Usa un cliente Docker SDK en patrón singleton opcional (_get_client) con degradación automática a subprocesos CLI cuando el SDK no está disponible.',
    functions: {
      _get_client: {
        summary: 'Inicializa y almacena en caché el cliente singleton del Docker SDK desde variables de entorno.',
        tags: ['docker-sdk', 'singleton', 'conexion'],
        complexity: 'simple'
      },
      compose_run: {
        summary: 'Ejecuta docker compose -f con soporte para capturar salida o heredar terminal.',
        tags: ['docker-compose', 'subproceso', 'ejecucion'],
        complexity: 'simple'
      },
      compose_output: {
        summary: 'Ejecuta un comando docker compose capturando su salida estándar limpia y código de retorno.',
        tags: ['docker-compose', 'subproceso', 'captura'],
        complexity: 'simple'
      },
      compose_passthrough: {
        summary: 'Ejecuta docker compose con herencia completa de terminal para streaming interactivo.',
        tags: ['docker-compose', 'passthrough', 'streaming'],
        complexity: 'simple'
      },
      docker_run: {
        summary: 'Ejecuta comandos directos de la CLI docker como alternativa cuando el SDK no aplica.',
        tags: ['docker', 'subproceso', 'fallback'],
        complexity: 'simple'
      },
      is_service_running: {
        summary: 'Determina si al menos un contenedor de un compose file está activo mediante ps -q.',
        tags: ['docker-compose', 'estado', 'contenedores'],
        complexity: 'simple'
      },
      get_container_ids: {
        summary: 'Devuelve la lista de IDs de contenedores activos asociados a un archivo compose.',
        tags: ['docker-compose', 'contenedores', 'consulta'],
        complexity: 'simple'
      },
      container_inspect: {
        summary: 'Inspecciona atributos de un contenedor usando mapeo rápido del SDK para templates comunes o docker inspect como fallback.',
        tags: ['docker-sdk', 'inspeccion', 'contenedores'],
        complexity: 'moderate'
      },
      get_container_stats: {
        summary: 'Obtiene una lectura puntual de estadísticas de CPU y memoria de un contenedor vía Docker SDK.',
        tags: ['docker-sdk', 'metricas', 'estadisticas'],
        complexity: 'simple'
      },
      get_container_info: {
        summary: 'Recupera nombre, estado, imagen, puertos, reinicios y health de un contenedor mediante Docker SDK.',
        tags: ['docker-sdk', 'inspeccion', 'metadatos'],
        complexity: 'simple'
      },
      list_all_containers: {
        summary: 'Lista contenedores activos o totales mediante Docker SDK devolviendo sus metadatos básicos.',
        tags: ['docker-sdk', 'listado', 'contenedores'],
        complexity: 'simple'
      },
      get_networks: {
        summary: 'Enumera redes Docker personalizadas y los contenedores e IPs conectados usando el SDK.',
        tags: ['docker-sdk', 'redes', 'inspeccion'],
        complexity: 'moderate'
      },
      sdk_available: {
        summary: 'Verifica si el Docker SDK está instalado y responde al comando ping.',
        tags: ['docker-sdk', 'verificacion', 'disponibilidad'],
        complexity: 'simple'
      }
    }
  },
  'svc_py/ui.py': {
    summary: 'Utilidades compartidas de interfaz Rich para el CLI svc, incluyendo consola global, mensajes estilizados, indicadores de estado y constructor de tablas.',
    tags: ['ui', 'rich', 'tablas', 'formato', 'utilidades'],
    complexity: 'moderate',
    functions: {
      error: {
        summary: 'Imprime un mensaje de error formateado con símbolo de cruz en rojo.',
        tags: ['ui', 'logging', 'error'],
        complexity: 'simple'
      },
      warn: {
        summary: 'Imprime una advertencia formateada con símbolo de alerta en amarillo.',
        tags: ['ui', 'logging', 'advertencia'],
        complexity: 'simple'
      },
      success: {
        summary: 'Imprime un mensaje de éxito formateado con símbolo de check en verde.',
        tags: ['ui', 'logging', 'exito'],
        complexity: 'simple'
      },
      info: {
        summary: 'Imprime un mensaje informativo formateado con símbolo de información en cian.',
        tags: ['ui', 'logging', 'informacion'],
        complexity: 'simple'
      },
      header: {
        summary: 'Renderiza un encabezado dentro de un Panel Rich con título y subtítulo opcional.',
        tags: ['ui', 'rich', 'panel'],
        complexity: 'simple'
      },
      status_dot: {
        summary: 'Devuelve un indicador visual verde o rojo según si el servicio está activo.',
        tags: ['ui', 'estado', 'indicador'],
        complexity: 'simple'
      },
      health_colored: {
        summary: 'Aplica color Rich al estado de healthcheck (healthy, unhealthy, starting).',
        tags: ['ui', 'salud', 'formato'],
        complexity: 'simple'
      },
      restart_colored: {
        summary: 'Colorea el contador de reinicios según su severidad.',
        tags: ['ui', 'reinicios', 'formato'],
        complexity: 'simple'
      },
      service_table: {
        summary: 'Construye una Table Rich con estilo redondeado y columnas configurables para listar servicios.',
        tags: ['ui', 'rich', 'tabla'],
        complexity: 'simple'
      },
      confirm_action: {
        summary: 'Muestra en consola la acción que está por ejecutarse sobre un servicio.',
        tags: ['ui', 'confirmacion', 'feedback'],
        complexity: 'simple'
      }
    }
  }
};

// Build nodes & edges per file
const nodesByFile = {};
const edgesBySourceFile = {};
const fileFuncs = {};

for (const r of extract.results) {
  fileFuncs[r.path] = new Set((r.functions || []).map(f => f.name));
}

function addEdge(filePath, edge) {
  if (edge.source === edge.target) return;
  const list = (edgesBySourceFile[filePath] ||= []);
  const key = `${edge.source}|${edge.target}|${edge.type}`;
  if (!list.some(e => `${e.source}|${e.target}|${e.type}` === key)) {
    list.push(edge);
  }
}

for (const r of extract.results) {
  const fp = r.path;
  const spec = FILE_SPECS[fp];
  if (!spec) throw new Error(`Missing FILE_SPECS for ${fp}`);

  const fileNodeId = `file:${fp}`;
  const fileNode = {
    id: fileNodeId,
    type: 'file',
    name: path.posix.basename(fp),
    filePath: fp,
    summary: spec.summary,
    tags: spec.tags,
    complexity: spec.complexity,
  };
  if (spec.languageNotes) {
    fileNode.languageNotes = spec.languageNotes;
  }

  const fNodes = [fileNode];
  const exportsSet = new Set((r.exports || []).map(e => e.name));

  for (const fn of (r.functions || [])) {
    const lineCount = fn.endLine - fn.startLine + 1;
    const isExported = exportsSet.has(fn.name);
    if (lineCount < 10 && !isExported) continue;

    const fnSpec = spec.functions[fn.name];
    if (!fnSpec) throw new Error(`Missing fn spec for ${fp}:${fn.name}`);
    const fnId = `function:${fp}:${fn.name}`;
    fNodes.push({
      id: fnId,
      type: 'function',
      name: fn.name,
      filePath: fp,
      lineRange: [fn.startLine, fn.endLine],
      summary: fnSpec.summary,
      tags: fnSpec.tags,
      complexity: fnSpec.complexity,
    });

    addEdge(fp, {
      source: fileNodeId,
      target: fnId,
      type: 'contains',
      direction: 'forward',
      weight: 1.0,
    });

    if (isExported) {
      addEdge(fp, {
        source: fileNodeId,
        target: fnId,
        type: 'exports',
        direction: 'forward',
        weight: 0.8,
      });
    }
  }

  nodesByFile[fp] = fNodes;

  // 1:1 imports edges from batchImportData
  for (const targetPath of (meta.batchImportData[fp] || [])) {
    addEdge(fp, {
      source: fileNodeId,
      target: `file:${targetPath}`,
      type: 'imports',
      direction: 'forward',
      weight: 0.7,
    });
  }

  // Calls edges from callGraph within batch 1
  const imports = meta.batchImportData[fp] || [];
  const ownFuncs = fileFuncs[fp];
  for (const c of (r.callGraph || [])) {
    if (!c.caller || !ownFuncs.has(c.caller)) continue;
    const callee = c.callee;
    const srcFnId = `function:${fp}:${c.caller}`;

    if (ownFuncs.has(callee) && callee !== c.caller) {
      addEdge(fp, {
        source: srcFnId,
        target: `function:${fp}:${callee}`,
        type: 'calls',
        direction: 'forward',
        weight: 0.8,
      });
    }

    for (const imp of imports) {
      if (fileFuncs[imp] && fileFuncs[imp].has(callee)) {
        addEdge(fp, {
          source: srcFnId,
          target: `function:${imp}:${callee}`,
          type: 'calls',
          direction: 'forward',
          weight: 0.8,
        });
      }
      const parts = callee.split('.');
      if (parts.length === 2 && fileFuncs[imp] && fileFuncs[imp].has(parts[1])) {
        addEdge(fp, {
          source: srcFnId,
          target: `function:${imp}:${parts[1]}`,
          type: 'calls',
          direction: 'forward',
          weight: 0.8,
        });
      }
    }
  }
}

// Explicit dynamic/deferred intra-batch calls & file-level depends_on
// app.py registers subcommands from svc_py/commands/*.py
for (const mod of [
  'svc_py/commands/health.py',
  'svc_py/commands/docker.py',
  'svc_py/commands/backup.py',
  'svc_py/commands/info.py',
  'svc_py/commands/compose.py',
  'svc_py/commands/menu.py',
  'svc_py/commands/catalog.py',
  'svc_py/commands/scanner.py',
  'svc_py/commands/codemap.py',
]) {
  addEdge('svc_py/app.py', {
    source: 'file:svc_py/app.py',
    target: `file:${mod}`,
    type: 'depends_on',
    direction: 'forward',
    weight: 0.6,
  });
}

// menu.py _execute_action deferred imports/calls
for (const [targetFile, targetFn] of [
  ['svc_py/commands/backup.py', 'backup'],
  ['svc_py/commands/backup.py', 'restore'],
  ['svc_py/commands/info.py', 'depends'],
  ['svc_py/commands/info.py', 'env_cmd'],
  ['svc_py/commands/info.py', 'open_cmd'],
]) {
  addEdge('svc_py/commands/menu.py', {
    source: 'function:svc_py/commands/menu.py:_execute_action',
    target: `function:${targetFile}:${targetFn}`,
    type: 'calls',
    direction: 'forward',
    weight: 0.8,
  });
  addEdge('svc_py/commands/menu.py', {
    source: 'file:svc_py/commands/menu.py',
    target: `file:${targetFile}`,
    type: 'depends_on',
    direction: 'forward',
    weight: 0.6,
  });
}

// bash_bridge.py fallback import to discovery.py
addEdge('svc_py/core/bash_bridge.py', {
  source: 'function:svc_py/core/bash_bridge.py:svc_list_services',
  target: 'function:svc_py/core/discovery.py:svc_list',
  type: 'calls',
  direction: 'forward',
  weight: 0.8,
});
addEdge('svc_py/core/bash_bridge.py', {
  source: 'file:svc_py/core/bash_bridge.py',
  target: 'file:svc_py/core/discovery.py',
  type: 'depends_on',
  direction: 'forward',
  weight: 0.6,
});

// Subprocess / external script dependencies verified in scan-result.json
for (const [srcFile, targetFile] of [
  ['svc_py/commands/codemap.py', 'agent/tools/project_index.py'],
  ['svc_py/commands/scanner.py', 'agent/tools/project_scanner.py'],
  ['svc_py/commands/compose.py', 'agent/tools/compare_tools.py'],
  ['svc_py/commands/catalog.py', 'docker/cli/lib/catalog-sync.sh'],
  ['svc_py/commands/catalog.py', 'agent/catalog/_index.py'],
  ['svc_py/core/bash_bridge.py', 'docker/cli/svc.sh'],
]) {
  addEdge(srcFile, {
    source: `file:${srcFile}`,
    target: `file:${targetFile}`,
    type: 'depends_on',
    direction: 'forward',
    weight: 0.6,
  });
}

const allNodes = Object.values(nodesByFile).flat();
const allEdges = Object.values(edgesBySourceFile).flat();

const nodeCount = allNodes.length;
const edgeCount = allEdges.length;
const importEdgesCount = allEdges.filter(e => e.type === 'imports').length;
const expectedImports = Object.values(meta.batchImportData).reduce((a, b) => a + b.length, 0);
if (importEdgesCount !== expectedImports) {
  throw new Error(`Import edge mismatch: ${importEdgesCount} != ${expectedImports}`);
}

// Check duplicate IDs
const nodeIdSet = new Set();
for (const n of allNodes) {
  if (nodeIdSet.has(n.id)) throw new Error(`Duplicate node ID: ${n.id}`);
  nodeIdSet.add(n.id);
}

const sortedFiles = Object.keys(nodesByFile).sort();
const parts = Math.ceil(Math.max(nodeCount / 60, edgeCount / 120));
const chunkSize = Math.ceil(sortedFiles.length / parts);

console.log(`Total nodes: ${nodeCount}, Total edges: ${edgeCount}, Imports: ${importEdgesCount}/${expectedImports}, Parts: ${parts}, ChunkSize: ${chunkSize}`);

for (let i = 0; i < parts; i++) {
  const chunkFiles = sortedFiles.slice(i * chunkSize, (i + 1) * chunkSize);
  const partNodes = chunkFiles.flatMap(fp => nodesByFile[fp]);
  const partEdges = chunkFiles.flatMap(fp => edgesBySourceFile[fp] || []);
  const outPath = `${UA_DIR}/intermediate/batch-1-part-${i + 1}.json`;
  fs.writeFileSync(outPath, JSON.stringify({ nodes: partNodes, edges: partEdges }, null, 2), 'utf8');
  console.log(`Wrote ${outPath}: ${partNodes.length} nodes, ${partEdges.length} edges (files: ${chunkFiles.join(', ')})`);
}
