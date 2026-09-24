# Firefox Newtab Plugin

Skills and tools for Firefox newtab development.

## Skills

### `nova-cleanup-comments`

Adds `@nova-cleanup` comments to Firefox newtab code for Project Nova parallel implementation tracking.

Use this skill when adding cleanup comments to Nova-related changes. See [`skills/nova-cleanup-comments/SKILL.md`](skills/nova-cleanup-comments/SKILL.md) for details.

### `backend-investigation`

Diagnostic workflow for Home New Tab **backend** incidents, covering content recommendations, Picture of the Day, the daily crossword, and other New Tab features served the same way. It produces an evidence-backed `FINDINGS.md` with a root cause, quantified impact, and the change that would resolve it.

Use this skill when a Sentry alert fires, an editor reports something broken, or a New Tab feature looks empty, wrong, or stale. It works with whatever access you already have, and where it needs a tool or a credential it does not have, it tells you what to install or request and how. See [`skills/backend-investigation/SKILL.md`](skills/backend-investigation/SKILL.md) for details.
