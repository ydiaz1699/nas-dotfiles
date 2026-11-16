# Reglas y Directivas para Google Antigravity CLI en el NAS

## 1. Idioma
- Responde siempre en español al interactuar con el usuario.
- Mantén las explicaciones técnicas claras, precisas y directas.

## 2. NextDNS — Mapeo de Usuarios
- Cuando el usuario mencione "yo", "mi", "infinix" o "mi teléfono", utiliza las tools del servidor MCP `nextdns-infinix` (perfil `2511f5`).
- Cuando el usuario mencione "papá" o "mi papá", utiliza las tools del servidor MCP `nextdns-papa` (perfil `2f6df5`).
- No cruces perfiles ni modifiques listas de un usuario sin indicación explícita.
- Para bloquear servicios como YouTube, utiliza `manageLists` con `list_type=parental_services`.

## 3. Filosofía del Servidor NAS
- Rutas del framework: `$NAS_DOTFILES` (`/nas-dotfiles`), `$dkco` (`/docker`), `$aadm` (`/home/aadm`).
- No expongas contraseñas, tokens ni API keys en texto claro en logs ni mensajes.
- Siempre confirma antes de ejecutar operaciones destructivas (borrados, resync total, detención de servicios críticos).
