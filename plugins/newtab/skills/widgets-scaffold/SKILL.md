---
description: Scaffolds a new Firefox New Tab widget with JSX, SCSS, prefs, telemetry, Widgets.jsx integration, and a draft test file. Use when the user wants to add a new widget to the New Tab page.
---

# New Tab Widget Scaffold

Widgets live in `browser/extensions/newtab/content-src/components/Widgets/{Name}/`.

## Workflow

### Step 1 — Gather requirements

Ask the user to run the requirements script first:

```
python3 {BASE_DIR}/scripts/gather_requirements.py
```

The script asks all required questions and prints a widget spec summary.
Wait for the user to paste that summary before proceeding.

### Step 2 — Plan

Enter plan mode. Using the spec and the example in
`references/ExampleWidget/`, propose the full list of files to
create/modify before writing anything. Read `references/notes.md` for
non-obvious requirements and gotchas.

Files touched by every widget:
1. `ActivityStream.sys.mjs` — register prefs (**do this first, then run `./mach build faster` before proceeding**)
2. `Widgets/{Name}/{Name}.jsx` — new widget component. Add `PREF_NOVA_ENABLED = "nova.enabled"` and `PREF_{NAME}_SIZE = "widgets.{widgetKey}.size"` constants. Derive size as `prefs[PREF_{NAME}_SIZE] || "medium"`. After all hooks, add a `// @nova-cleanup(remove-gate)` comment followed by `if (!prefs[PREF_NOVA_ENABLED]) { return null; }` to gate the widget on Nova being enabled. Apply `col-4 ${widgetSize}-widget` unconditionally on the root element. Use the submenu pattern for resize (see notes.md — "Widget resize context menu"); do NOT use separate `<panel-item hidden={...}>` elements. Check `supportsSmallSize` from the spec — if `yes`, add `"small"` to the size map in the submenu.
3. `Widgets/{Name}/_{Name}.scss` — widget styles. Add `&.medium-widget { grid-row: span 2; }` and `&.large-widget { grid-row: span 4; }` inside the root class. Add `&.small-widget { grid-row: span 1; }` only if `supportsSmallSize = yes`.
4. `Widgets/Widgets.jsx` — import, enabled logic, null guard, JSX render
5. `Widgets/_Widgets.scss` — add CSS class to `:has()` selector
6. `test/jest/content-src/components/Widgets/{Name}.test.jsx` — create a dedicated test file for the new widget. The shared `Widgets.test.jsx` is for container/integration coverage only; per-widget tests live in their own file alongside the other widgets in that directory (e.g. `FocusTimer.test.jsx`, `Weather.test.jsx`)
7. `content-src/styles/activity-stream.scss` — add `@import`
8. `content-src/styles/nova/activity-stream.scss` — add `@import` (**required — without this, styles won't render in Nova mode**)
9. `stylelint-rollouts.config.js` (repo root) — add the new widget's SCSS path in alphabetical order alongside the other widget entries
10. `Base.jsx`, `CustomizeMenu.jsx`, `ContentSection.jsx`, `WidgetsManagementPanel.jsx` — Customize panel toggle (add prop to function signature, switch case, and `moz-toggle` in `WidgetsManagementPanel.jsx`)
11. `AboutPreferences.sys.mjs` — register prefs, settings, and items in the Home group (`about:preferences#home`), set up in `_setupHomeGroup`
12. `browser/locales/en-US/browser/newtab/newtab.ftl` — FTL strings for new tab
13. `browser/locales/en-US/browser/preferences/preferences.ftl` — FTL string for `about:preferences` toggle

Additional files if the spec requires them:
- `common/Actions.mjs` + `common/Reducers.sys.mjs` — only if Redux state is needed

### Step 3 — Scaffold

After plan approval, implement all files end-to-end without stopping between
edits. Do not pause to summarize progress or ask for confirmation mid-scaffold.
Work through every file in the plan in sequence, replicating the patterns in
`references/ExampleWidget/` and substituting values from the spec.

Only stop if you hit a genuine blocker (e.g. a file doesn't exist where expected,
or the codebase structure differs from what the plan assumed). In that case,
explain what you found and what decision is needed before continuing.

### Step 4 — Build and verify

After scaffolding, the build artifacts must be regenerated:

1. `./mach newtab bundle` — compile SCSS and JS (**`./mach build faster` alone does NOT recompile SCSS**)
2. `./mach build faster` — copy compiled artifacts to the build output
3. Commit the build artifacts: `css/activity-stream.css`, `css/nova/activity-stream.css`, `data/content/activity-stream.bundle.js`

### Step 5 — Follow-up

**Always output this section in full after Step 4 — do not skip or summarize it.**

Tell the user:
- Add any remaining Fluent strings for context menu items and widget body labels
- Run `./mach lint`

Then output the full enable instructions below:

**Option A — `about:config`**

Set **all three** of these to `true`:
- `browser.newtabpage.activity-stream.widgets.system.enabled` (parent gate for all widgets — defaults to `false`)
- `browser.newtabpage.activity-stream.widgets.{widgetKey}.enabled`
- `browser.newtabpage.activity-stream.widgets.system.{widgetKey}.enabled`

**Option B — Nimbus trainhop**

1. Install [Nimbus devtools](https://github.com/mozilla-extensions/nimbus-devtools/releases/tag/release%2Fv0.3.0)
2. Choose "Feature configuration enrollment" on the left side
3. Opt into an experiment for `newtabTrainhop` with:

```json
{
  "type": "widgets",
  "payload": {
    "enabled": true,
    "{widgetKey}Enabled": true
  }
}
```
