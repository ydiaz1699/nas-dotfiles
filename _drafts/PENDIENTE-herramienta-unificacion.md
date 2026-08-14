# PENDIENTE — Herramienta de unificación de documentos

## Contexto

En otra sesión de chat se creó (o se diseñó) una herramienta/meta-prompt para
unificar fragmentos dispersos en una guía coherente. Necesito ubicarla.

## Qué debe hacer la herramienta

1. Leer N fragmentos de un tema (pueden ser de distintas fuentes: ChatGPT, Kimi, notas propias)
2. Deduplicar contenido repetido
3. Unificar en un solo documento con estructura estándar
4. Respetar el orden de ejecución (mkdir → archivos → permisos → levantar)
5. Producir una guía portable (autocontenida, sin depender del framework)

## Qué hacer

- [ ] Buscar en el otro chat si la herramienta se creó
- [ ] Si existe: copiar a `$NAS_DOTFILES/agent/tools/` o `$NAS_DOTFILES/docs/meta-prompts/`
- [ ] Si no existe: crearla (puede ser un meta-prompt .md o un script Python)
- [ ] Poner la ruta aquí y volver al chat de "revisar nas-dotfiles y actualizar docs" para usarla

## Ruta de la herramienta (llenar cuando se encuentre/cree)

```
RUTA: $NAS_DOTFILES/docs/meta-prompt-unificar.md ✅ ENCONTRADA
```

## Estado: RESUELTO

La herramienta existe y está documentada. Es un meta-prompt que se copia
al inicio de cualquier chat LLM para que unifique fragmentos dispersos.
Incluye variante para documentos largos (análisis por partes).

## Referencia

- Chat donde se usó por primera vez: el de unificación de filebrowser (este chat actual)
- Resultado manual: `docs/services/filebrowser-guide.md` (5790 líneas → 304 líneas)
