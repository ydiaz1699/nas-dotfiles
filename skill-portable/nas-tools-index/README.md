# nas-tools-index — skill portable

Versión **portable y autocontenida** del índice de herramientas del framework
`nas-dotfiles`. Sirve para pasarle a **otro LLM** (Claude, un Kiro nuevo, modelo
local) el conocimiento de **una** herramienta sin volcar todo el framework.

- Fuente viva (requiere el repo): `docs/tools-index.md`
- Esta carpeta es el **espejo portable** → se empaqueta en `.zip` y se sube.

## Empaquetar

```bash
cd skill-portable
zip -r nas-tools-index-skill.zip nas-tools-index
# (si no hay zip: python3 -c "import shutil; shutil.make_archive('nas-tools-index-skill','zip','.','nas-tools-index')")
```

El `.zip` se regenera, por eso va en `.gitignore`.

## Subir

- **Kiro**: Settings → Skills → "+ Add skill" → seleccionar el `.zip`.
- **Claude**: subir como Agent Skill (mismo `.zip`).

## Usar

Pregunta al LLM, p. ej.: *"¿qué es `bat` en mi framework?"* → responde desde el
índice sin el repo. También incluye `scripts/tool-lookup.sh <nombre>` para grep local.

## Mantenimiento (es un espejo)

Si cambias `docs/tools-index.md`, regenera `SKILL.md` aquí, re-empaqueta el `.zip`
y vuelve a subirlo. **No se sincroniza solo.**
