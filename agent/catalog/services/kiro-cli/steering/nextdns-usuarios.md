# NextDNS — Mapa de Usuarios y Perfiles

- "yo" / "mi" / "infinix" / "mi teléfono" → usar servidor `nextdns-infinix` (perfil `2511f5`).
- "papá" / "mi papá" → usar servidor `nextdns-papa` (perfil `2f6df5`).

Usa ÚNICAMENTE las tools del servidor MCP que corresponde al usuario solicitado.
Para bloquear servicios (como YouTube): invoca `manageLists` con `list_type=parental_services`. Si ya existe en la lista con `active: false`, actívalo con `operation=update`.
