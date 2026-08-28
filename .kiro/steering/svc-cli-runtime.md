# Compatibilidad del CLI `svc` en el NAS

Estas reglas son obligatorias para cualquier guía, diagnóstico o comando generado para `nas-dotfiles`.

## Dos implementaciones

El shell expone dos entradas:

- `NAS_CLI=bash`: `docker/cli/svc.sh`, passthrough Bash; es la predeterminada salvo que el entorno cambie el valor.
- `NAS_CLI=python`: `python3 -m svc_py`, CLI Typer/Rich.

No mezclar ejemplos de una implementación con la otra. En procedimientos paste-safe, fijar explícitamente `NAS_CLI=bash` o `NAS_CLI=python`.

## `svc exec`

Bash y Python reciben argumentos distintos:

```bash
# Bash: proyecto/compose, servicio interno, comando.
NAS_CLI=bash svc exec lobehub lobehub-mcp python -c 'print("ok")'
NAS_CLI=bash svc exec lobehub /bin/node -e 'console.log("ok")'

# Python/Typer: proyecto/compose, separador de Typer, servicio interno opcional, comando.
NAS_CLI=python svc exec lobehub -- lobehub-mcp python -c 'print("ok")'
NAS_CLI=python svc exec lobehub -- /bin/node -e 'console.log("ok")'
```

En Python, `--` separa las opciones de Typer del comando interno. Debe aparecer antes de cualquier argumento como `-c`, `-e`, `-U`, `-d`, `-v` o `-T`; si se omite, Typer puede responder `No such option`. `-T` no está registrado por el CLI Python y no debe usarse.

En Python, el primer argumento después de `svc exec` selecciona el compose. Para el stack LobeHub, `lobehub` es el compose y `lobehub-mcp` es el servicio interno; por eso no se debe repetir `lobehub` como servicio cuando se quiere ejecutar dentro del contenedor `lobehub`, y para MCP se usa `NAS_CLI=python svc exec lobehub -- lobehub-mcp ...`. La forma antigua `svc exec lobehub lobehub-mcp -- python -c ...` es inválida porque mezcla ambas gramáticas.

## Contexto y secretos

- `root@Nas ... #` ejecuta Bash; `aipostgres=#`/`*_db=>` ejecuta SQL/psql. Siempre salir con `\q` antes de volver a Bash.
- Si se leen `$dkco/.env` o se resuelve Compose, usar root o entrar al servicio con `dk <servicio>`; un usuario sin permisos desde `~` puede obtener `open /docker/.env: permission denied`.
- Nunca imprimir o compartir `.env`, tokens o `svc config` resuelto.
- `Endpoint:`, `Auth type:` y `API Key:` son campos de una interfaz web, no comandos Bash.
- No usar `exit` en un bloque pegado directamente en una shell interactiva; usar subshell o ramas `if/else` para no cerrar accidentalmente SSH.

## Diagnóstico MCP

- Probar la red desde el contenedor LobeHub con el hostname interno `lobehub-mcp`.
- Una petición POST sin Bearer debe devolver `401`; eso confirma red, DNS y ruta.
- Una petición autenticada `tools/list` desde el sidecar debe devolver `200` y cinco tools.
- No abrir `http://lobehub-mcp:8790/mcp` en el navegador: es un endpoint POST interno y un GET devuelve `405` por diseño.


## Integración MCP de LobeHub

- Configurar el cliente como **Streamable HTTP** con endpoint `http://lobehub-mcp:8790/mcp` y **API Key** en la UI; pegar el token sin `Bearer`. No importar inicialmente un header JSON manual ni publicar el puerto `8790`.
- `lobehub-mcp` es resoluble únicamente desde el backend de LobeHub dentro de `lobe_storage`; el navegador no debe abrir ese hostname. Un GET puede devolver `405` por diseño porque el flujo válido es POST JSON-RPC.
- Evidencia de aceptación: POST sin token devuelve `401`; `tools/list` autenticado devuelve `200`, `application/json; charset=utf-8` y `tools_count=5`. `svc lobehub verify` debe terminar con `Resultado: 0 fallos`; `QSTASH_TOKEN not set` es un aviso opcional.
- “Migración PostgreSQL” significa que LobeHub migró `lobehub_db` dentro de `datapostgres` de DataSQL; no implica crear otro PostgreSQL. Mantener `lobehub_user` dedicado y mínimo privilegio.
- En una sesión interactiva, texto como `Endpoint:`/`Auth type:`/`API Key:` se copia solo en la UI, nunca en Bash. Si aparece `csl: orden no encontrada`, se pegó contenido de presentación en la terminal.
