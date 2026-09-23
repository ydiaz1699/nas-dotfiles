# Verificar contra la fuente real ANTES de entregar código/comandos

Regla obligatoria para cualquier LLM que genere un Dockerfile, `compose.yml`,
comando ejecutable o instrucción de instalación para `nas-dotfiles` (o el entorno del
usuario). El objetivo es entregar algo que **funcione a la primera**, no "probar y
corregir" por no haber verificado lo que sí estaba disponible.

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
