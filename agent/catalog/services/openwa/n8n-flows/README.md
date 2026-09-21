# Workflows n8n para OpenWA

Flujos de ejemplo listos para importar en n8n, verificados contra el nodo real
`@rmyndharis/n8n-nodes-openwa` (repo `rmyndharis/OpenWA-n8n`).

## Requisito previo

Instalar el nodo community **oficial** en n8n:
**Settings → Community Nodes → Install** → `@rmyndharis/n8n-nodes-openwa`

> ⚠️ El paquete es **con scope**: `@rmyndharis/n8n-nodes-openwa`. Los tipos de
> nodo internos son `@rmyndharis/n8n-nodes-openwa.openWa` y
> `@rmyndharis/n8n-nodes-openwa.openWaTrigger`. Si en algún JSON aparece el tipo
> SIN el scope (`n8n-nodes-openwa.*`), n8n intenta instalar un segundo paquete
> con ese nombre y quedan DOS paquetes duplicados en conflicto. En ese caso,
> desinstalar el duplicado sin scope desde Settings → Community Nodes y dejar
> solo `@rmyndharis/n8n-nodes-openwa`.

## Flujos incluidos

| Archivo | Qué hace |
|---|---|
| `auto-reply.json` | Recibe mensaje → si contiene "hola" → responde al remitente |
| `echo-simple.json` | Recibe cualquier mensaje → responde con eco (sin filtro) |

## Cómo importar

1. En n8n: menú **⋮** (arriba a la derecha) → **Import from File / Clipboard**.
2. Pega o sube el JSON.

## Ajustes obligatorios tras importar

Al importar, n8n **no** vincula la credencial ni resuelve el UUID. En cada nodo
OpenWA (Trigger y acción):

1. **Credential:** seleccionar tu credencial **"OpenWA API"** en el desplegable.
   - Credencial: Server URL `http://openwa:2785`, API Key = `API_MASTER_KEY`.
2. **Session Name or ID:** abrir el desplegable y elegir la sesión (p.ej.
   `prueba`). El nodo pone el UUID correcto solo — NO escribir el `name` a mano.
   - El `REEMPLAZA_ID_CREDENCIAL` y el UUID del JSON son placeholders; el
     desplegable los sustituye por los valores reales de tu instancia.

## Probar

1. Abrir el nodo Trigger → **Listen for test event**.
2. Enviar un WhatsApp (con "hola" para `auto-reply.json`) al número vinculado.
3. n8n captura el evento; se ve la estructura real bajo `$json.data`.
4. Activar el workflow (toggle **Active**) para que quede en automático.

## Estructura del evento (para expresiones)

El Trigger entrega un envelope; los datos del mensaje van bajo `data`:

| Campo | Uso |
|---|---|
| `{{ $json.data.chatId }}` | a quién responder |
| `{{ $json.data.body }}` | texto recibido |
| `{{ $json.data.from }}` | remitente |
| `{{ $json.data.type }}` | tipo (`text`, `image`...) |
| `{{ $json.idempotencyKey }}` | deduplicar reintentos |

## Recursos y operaciones del nodo OpenWA (acción)

19 recursos: Session, Message, Chat, Contact, Group, Channel, Label, Media,
Catalog, Status, Presence, Profile, Call, Template, Automation Rule, Webhook,
API Key, System, Observability. El campo del texto en `Message → Send Text` se
llama **Message** (no "Text").
