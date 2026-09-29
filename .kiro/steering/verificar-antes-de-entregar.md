# Verificar contra la fuente real ANTES de entregar código/comandos

Regla obligatoria para cualquier LLM que genere un Dockerfile, `compose.yml`,
comando ejecutable o instrucción de instalación para `nas-dotfiles` (o el entorno del
usuario). El objetivo es entregar algo que **funcione a la primera**, no "probar y
corregir" por no haber verificado lo que sí estaba disponible.

## Paso 0 (PRIMERO DE TODO): consultar la doc INTERNA que YA existe

Antes de producir NADA, leer la documentación interna del tema. El error más común
NO es equivocarse con una fuente externa, sino **empezar a generar sin leer lo que el
repo/ecosistema ya tiene escrito** — repitiendo trabajo, pidiendo datos ya
documentados o ignorando convenciones establecidas. Consultar SIEMPRE, según la tarea:

| Si vas a... | LEE PRIMERO (obligatorio) |
|---|---|
| Crear/modificar un **servicio Docker** (compose, volúmenes, redes) | `agent/catalog/_compose_base.md` + `docs/docker-entorno.md` + `docs/services/<svc>-guide.md` y `agent/catalog/services/<svc>/ficha.md` si el servicio ya existe |
| Montar/tocar un **MCP en kiro-cli** (mcp_tools, permissions, wrapper, Dockerfile) | `Varios_tools/kiro-cli-nas/README.md` (mapa del entorno) + la guía del MCP concreto (`Varios_tools/kiro-cli-nas/<mcp>.md`) |
| Crear un **repo/proyecto nuevo** o recomendar herramienta/MCP | el índice maestro `repo-index` (skill o repo `ydiaz1699/repo-index`) |
| Tocar **arranque escalonado / layers.conf / restart policy** | `docs/docker-boot-staged-guide.md` |
| No saber qué componente del framework existe | `docs/framework-audit.md` (mapa ejecutivo) |

> **Regla de oro:** si el usuario tiene un repo cargado (nas-dotfiles, Varios_tools),
> la respuesta a "¿cómo se hace X aquí?" casi siempre YA está escrita. Buscarla ANTES
> de pedir datos al usuario o de inventar una convención. Pedir un dato que ya está
> documentado, o generar un compose sin seguir `_compose_base.md`, es el fallo a evitar.
>
> **Origen:** en la sesión de montaje de JDownloader se generó primero un `compose.yml`
> sin leer `_compose_base.md` (TZ inline, `extends` mal, sin labels) y se pidieron al
> usuario datos del entorno kiro-cli que ya estaban en `Varios_tools/kiro-cli-nas/`.
> Ambos evitables consultando la doc interna primero.

## No trabajar de memoria ni por suposición

NUNCA afirmar que un paquete/imagen/flag existe o se instala de cierta forma sin
comprobarlo. Verificar SIEMPRE contra la fuente real antes de entregar.

## Checklist previo a entregar un Dockerfile / instalación de un paquete externo

1. **¿El paquete existe donde asumo?** Comprobar el registro real antes de usar el
   gestor correspondiente:
   - PyPI: `curl -s -o /dev/null -w "%{http_code}" https://pypi.org/pypi/<paquete>/json`
     (404 = NO está en PyPI → instalar desde git/otra fuente, no `pip/uv tool install <nombre>`).
   - npm: `npm view <paquete> version` · Docker: `curl` a los tags del registro.
2. **¿Es un comando o un módulo?** Leer el `pyproject.toml`/`package.json` COMPLETO:
   - Si NO declara `[project.scripts]` (o `bin`), el paquete es un **módulo** → se
     invoca con `python -m <modulo>`, y `uv tool install` FALLA con
     `No executables are provided`. Usar `uv venv` + `uv pip install`.
3. **¿Algún volumen/mount tapa la ruta de instalación?** Si el binario se instala en
   `~/.local/bin` (o `$HOME/...`) y el compose monta un volumen sobre ese `$HOME`
   (ej. `./data:/home/<user>`), el volumen **oculta** la instalación en runtime
   (`executable not found`). Instalar FUERA del mount (ej. `/opt/...`).
4. **¿Permisos/UID?** Si el contenedor corre como un uid no-root y una carpeta/host la
   crea root, habrá `Permission denied`. Prever `chown <uid>:<uid>` o rutas accesibles
   (`UV_PYTHON_INSTALL_DIR=/opt/...`, `chmod -R a+rX`).
5. **Leer archivos de config completos, no en trozos** (pyproject, README de
   instalación, healthcheck flags) antes de escribir el comando final.

## Origen de esta regla

Al montar `kiro-cli` (contenedor con Kiro CLI + MCPs), se entregaron 3 Dockerfiles
fallidos por saltarse este checklist: binario tapado por el volumen (punto 3),
`uv tool install` de un paquete que no estaba en PyPI (punto 1) y que además era un
módulo sin comando (punto 2). Todos evitables verificando antes. Ver
`docs/ideas-decisions.md` #24.

## Regla complementaria (ya existente)

Alinear con el flujo de PRs y verificación del repo: confirmar existencia de
repos/imágenes con `gh api`/`curl` antes de afirmar, y no reintroducir bloques
antiguos corregidos (ver `docs/ideas-decisions.md` y el steering `svc-cli-runtime.md`).
