---
name: widgets-scaffold
description: "Scaffolds a new Firefox New Tab widget end-to-end — generates JSX component, SCSS styles, pref registration, telemetry hooks, Customize panel toggle, about:preferences entry, Fluent strings, and a Jest test file. Use when creating a new widget for the Firefox New Tab page, adding a newtab widget component, or scaffolding widget boilerplate in the Firefox browser."
---

# New Tab Widget Scaffold

Scaffolds a complete Firefox New Tab widget from a requirements spec. Generates all required files (component, styles, prefs, telemetry, tests) and integrates with Widgets.jsx, the Customize panel, and about:preferences.

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

Enter plan mode. Using the spec and the example in `references/ExampleWidget/`, propose the full list of files to create/modify before writing anything.

Read `references/notes.md` before planning — it contains non-obvious requirements and gotchas (build ordering, dual SCSS imports, Nova gating, Customize panel passthrough) that are not visible from the example component alone.

#### Required files (every widget)

**Prefs and build (do first):**
1. `ActivityStream.sys.mjs` — register prefs, then run `./mach build faster` before proceeding

**Component and styles:**
2. `Widgets/{Name}/{Name}.jsx` — component with Nova gate, size derivation, telemetry, and resize submenu (see `references/ExampleWidget/` and `references/notes.md` for patterns)
3. `Widgets/{Name}/_{Name}.scss` — styles with `medium-widget` and `large-widget` grid spans (add `small-widget` only if `supportsSmallSize = yes`)

**Integration:**
4. `Widgets/Widgets.jsx` — import, enabled logic, null guard, JSX render
5. `Widgets/_Widgets.scss` — add CSS class to `:has()` selector
6. `content-src/styles/activity-stream.scss` — add `@import`
7. `content-src/styles/nova/activity-stream.scss` — add `@import` (required for Nova mode)
8. `stylelint-rollouts.config.js` (repo root) — add SCSS path in alphabetical order

**Customize panel (all four required):**
9. `Base.jsx` — compute `mayHave{Name}Widget` and pass to both `<CustomizeMenu>` renders
10. `CustomizeMenu.jsx` — forward the prop
11. `ContentSection.jsx` — add switch case and `moz-toggle`
12. `WidgetsManagementPanel.jsx` — add `moz-toggle`

**Preferences and localization:**
13. `AboutPreferences.sys.mjs` — register prefs, settings, and items in `_setupHomeGroup`
14. `browser/locales/en-US/browser/newtab/newtab.ftl` — FTL strings for new tab
15. `browser/locales/en-US/browser/preferences/preferences.ftl` — FTL string for about:preferences toggle

**Testing:**
16. `test/jest/content-src/components/Widgets/{Name}.test.jsx` — per-widget test file (the shared `Widgets.test.jsx` is for container tests only)

#### Conditional files

- `common/Actions.mjs` + `common/Reducers.sys.mjs` — only if the spec requires Redux state

### Step 3 — Scaffold

After plan approval, implement all files end-to-end without stopping between edits. Work through every file in the plan in sequence, replicating the patterns in `references/ExampleWidget/` and substituting values from the spec.

Only stop if you hit a genuine blocker (e.g. a file doesn't exist where expected, or the codebase structure differs from what the plan assumed).

### Step 4 — Build and verify

After scaffolding, regenerate build artifacts:

1. `./mach newtab bundle` — compile SCSS and JS (`./mach build faster` alone does NOT recompile SCSS)
2. `./mach build faster` — copy compiled artifacts to build output
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
