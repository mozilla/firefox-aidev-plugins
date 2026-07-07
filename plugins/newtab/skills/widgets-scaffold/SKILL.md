---
description: Scaffolds a new Firefox New Tab widget with a registry entry, JSX, SCSS, prefs, telemetry, customize-panel + about:preferences integration, and a draft test file. Use when the user wants to add a new widget to the New Tab page.
---

# New Tab Widget Scaffold

Widgets live in `browser/extensions/newtab/content-src/components/Widgets/{Name}/`.

The **Widget Registry** (`common/WidgetsRegistry.mjs`) is the single source of
truth for every widget. Adding a widget is now mostly declarative: you add one
registry entry plus one component-registry entry, and shared helpers
(`isWidgetEnabled`, `resolveWidgetSize`, `resolveWidgetHasSidebar`,
`getHideAllTargets`, `resolveWidgetOrder`), shared UI (`WidgetMenuFooter`,
`SizeSubmenu`, `MoveSubmenu`, `WidgetWrapper`), and the shared
`useWidgetTelemetry` hook do the wiring that used to be hand-copied into
`Widgets.jsx`, `Base.jsx`, and every widget's menu and telemetry. Do **not**
hand-wire enabled-logic, size derivation, hide-all, the null-guard, the menu
footer, or telemetry payloads anymore.

## Naming convention (read first)

The widget **id/key** and **telemetry name** must NOT contain the word
"widget" — they already live under the `widgets.` pref namespace, so a `*Widget`
suffix is redundant. Use `widgets.example.enabled`, telemetry `"example"` — not
`widgets.exampleWidget.enabled` / `"example_widget"`. The Sports widget shipped
with the redundant id `sportsWidget` and it caused a pref + telemetry bug that
had to be fixed (its `telemetryName` is `"sports"`). Treat the Sports `*Widget`
naming as legacy — do not copy it.

## Telemetry (do NOT touch metrics.yaml)

Widget telemetry is fully generic and already defined once for all widgets in
`browser/components/newtab/metrics.yaml`: `widgets_impression`,
`widgets_user_event`, `widgets_enabled`, `widgets_error`, and
`widgets_container_action`. Every event is keyed by `widget_name` (your
`telemetryName`) plus `widget_size`, `error_type`, `user_action`, etc.

A new widget therefore adds **nothing** to `metrics.yaml` and requires **no**
`./mach newtab channel-metrics-diff` run. It emits the shared events through the
`useWidgetTelemetry({ dispatch, widget, widgetSize })` hook, which returns
`impressionRef` (attach to the widget root — fires `widgets_impression` once via
its own IntersectionObserver), `recordUserAction(action, { source, value })`
(`widgets_user_event`), `recordEnabled` (`widgets_enabled`), `recordImpression`
(manual one-shot), and `recordError` (`widgets_error`). Do NOT hand-build these
payloads or wire up your own observer — the hook keys every event on the
registry entry's `telemetryName` for you.
Only edit `metrics.yaml` if the widget needs a genuinely new event shape that
the shared `widgets_*` events cannot express — which is rare. Never scaffold a
per-widget `widgets.{key}.*` metric.

## Workflow

### Step 1 — Gather requirements

Ask the user to run the requirements script first:

```
python3 {BASE_DIR}/scripts/gather_requirements.py
```

The script asks all required questions (including the registry fields:
`telemetryName`, `order`, `validSizes`, `defaultSize`, `hasSidebar`, trainhop
keys) and prints a widget spec plus a ready-to-paste `WIDGET_REGISTRY` entry.
Wait for the user to paste that summary before proceeding.

### Step 2 — Plan

Enter plan mode. Using the spec and the example in
`references/ExampleWidget/`, propose the full list of files to create/modify
before writing anything. Read `references/notes.md` for non-obvious requirements
and gotchas.

The registry-centric core (do these first, in order):

1. `common/WidgetsRegistry.mjs` — add the `WIDGET_REGISTRY` entry (next `order`
   integer) and export the widget's pref-key constants
   (`PREF_WIDGETS_{KEY}_ENABLED`, `PREF_{KEY}_SIZE`,
   `PREF_WIDGETS_SYSTEM_{KEY}_ENABLED`). This replaces the old per-component
   pref constants and the hand-wired enabled expressions — `isWidgetEnabled`
   derives everything from the entry.
2. `lib/ActivityStream.sys.mjs` — register the three prefs (**do this first,
   then run `./mach build faster` before proceeding**). The size pref's `value`
   is `""` (empty = "user hasn't chosen"; lets trainhop/`defaultSize` apply).
3. `Widgets/{Name}/{Name}.jsx` — the widget component. Mirror
   `references/ExampleWidget/ExampleWidget.jsx`:
   - Look up its entry once: `const ENTRY = WIDGET_REGISTRY.find(w => w.id === "{key}")`.
   - Derive size with `resolveWidgetSize(ENTRY, prefs)` — never read the size
     pref directly.
   - Accept the standard props: `dispatch`, `handleUserInteraction` (interactive
     widgets only), `isMaximized`, `widgetsMayBeMaximized`, `widgetEnabledMap`.
   - Emit telemetry through the `useWidgetTelemetry({ dispatch, widget: ENTRY,
     widgetSize })` hook: attach the returned `impressionRef` to the widget's
     root element and call `recordUserAction(action, { source })` for
     interactions. Do **not** hand-build `WIDGETS_IMPRESSION` /
     `WIDGETS_USER_EVENT` payloads or wire up your own `IntersectionObserver`.
   - Render the shared `<WidgetMenuFooter>` as the last child of the menu's
     `<panel-list>`; it owns the common trailing block in a fixed order
     (divider, Change size, Move, Hide widget, Learn more — Learn more opens in
     a new tab). Put widget-specific items **above** it. Pass the Change size
     submenu via the `sizeSubmenu` prop as `<SizeSubmenu submenuId=...
     sizes={[...]} checkedSize={widgetSize} onChangeSize={handleChangeSize} />`,
     gated on `widgetsMayBeMaximized` (pass `null` otherwise); include `"small"`
     only if `validSizes` has it. Do **not** hand-roll the size submenu,
     `MoveSubmenu`, the Hide item, or the Learn more item — that hand-rolled
     footer is exactly what drifted out of sync (Bug 2046045 / D306294). The
     footer's `onLearnMore` is only for the extra `learn_more` telemetry; it
     dispatches `OPEN_LINK` (with `where: "tab"`) itself.
   - Render its own `<article className="{css} widget col-4 ${widgetSize}-widget">`
     root. Do **not** add a per-widget Nova gate — the container (`Widgets.jsx`)
     renders `WIDGET_ROW_COMPONENTS` only in its Nova branch, so the widget already
     mounts only under Nova; a `nova.enabled` early return here is redundant.
     (Sports has one; it is legacy — do not copy it.)
4. `Widgets/WidgetsComponentRegistry.jsx` — add the component to
   `WIDGET_ROW_COMPONENTS`. If the spec has `hasSidebar: true`, also add a
   sidebar component to `WIDGET_SIDEBAR_COMPONENTS` — see
   `references/SidebarVariant.md` for that wiring.
5. `Widgets/Widgets.jsx` — add the widget's id to the hand-maintained
   `widgetEnabledMap` object (mirror the `clocks`/`sportsWidget` entries):
   `{key}: isWidgetEnabled(WIDGET_REGISTRY.find(w => w.id === "{key}"), prefs, widgetsEnabled)`.
   **This is the one place the container is NOT yet registry-driven** (see the
   `Bug 2034542` TODO above the map). The render loop gates every widget on
   `widgetEnabledMap[id]`, so a widget missing from this map silently never
   renders — even though its registry entry, component-registry entry, and prefs
   are all correct. This is the single most common reason a freshly-scaffolded
   widget shows nothing on `about:newtab`. (Until Bug 2034542 lands, "don't
   hand-wire enabled-logic into Widgets.jsx" has this one exception.)

The supporting files (each widget still touches these):

6. `Widgets/{Name}/_{Name}.scss` — styles. `@include widget-base-style` on the
   root (NOT `newtab-card-style`): it provides the shared per-size card height,
   hover, transitions, and `position: relative`. Including `newtab-card-style`
   directly leaves the card with no height, so a sparse or not-yet-wired widget
   body collapses. Add `&.medium-widget { grid-row: span 2; }` and
   `&.large-widget { grid-row: span 4; }` inside the root class; add
   `&.small-widget { grid-row: span 1; }` only if `validSizes` includes `"small"`.
7. `content-src/styles/activity-stream.scss` — add `@import` of the widget SCSS.
8. `stylelint-rollouts.config.js` (repo root) — add the SCSS path in alphabetical
   order alongside the other widget entries.
9. `lib/AboutPreferences.sys.mjs` + `browser/locales/en-US/browser/preferences/preferences.ftl`
   — register the widget for `about:preferences#home` (see notes.md) with a
   `home-prefs-{css-class}-header` string.
10. Customize panel toggle (all required, see notes.md):
   `Base.jsx` (compute `mayHave{Name}Widget` and pass it to **both**
   `<CustomizeMenu>` renders) → `CustomizeMenu.jsx` (passthrough) →
   `Nova/CustomizeMenu/WidgetsManagementPanel/WidgetsManagementPanel.jsx` (add
   the `moz-toggle`) → `ContentSection.jsx` (classic path) →
   `browser/locales/en-US/browser/newtab/newtab.ftl` (toggle label).
11. `test/jest/content-src/components/Widgets/{Name}.test.jsx` — a dedicated Jest
    test file. New tests go in Jest (not the legacy `test/unit/` Enzyme suite).
    Note: `WidgetsRegistry.test.jsx` has hardcoded expected widget-order arrays —
    adding an entry breaks them until you append the new id (in registry order).

Additional files only if the spec requires them:
- `common/Actions.mjs` + `common/Reducers.sys.mjs` — only if Redux state is
  needed. New `WIDGETS_*` action types must stay alphabetically sorted (a test
  asserts it).
- `lib/{Name}Feed.sys.mjs` — only if the widget needs a backend data feed (see
  `WeatherFeed.sys.mjs`).

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

1. `./mach newtab bundle` — compile SCSS and JS (**`./mach build faster` alone
   does NOT recompile SCSS**)
2. `./mach build faster` — copy compiled artifacts to the build output
3. Commit the build artifacts: `css/activity-stream.css`,
   `css/nova/activity-stream.css`, `data/content/activity-stream.bundle.js`

### Step 5 — Follow-up

**Always output this section in full after Step 4 — do not skip or summarize it.**

Tell the user:
- Add any remaining Fluent strings for context menu items and widget body labels
- Run `./mach lint`

Then output the full enable instructions below:

**Option A — `about:config`**

Set **all three** of these to `true`:
- `browser.newtabpage.activity-stream.widgets.system.enabled` (parent gate for all widgets — defaults to `false`)
- `browser.newtabpage.activity-stream.widgets.{key}.enabled`
- `browser.newtabpage.activity-stream.widgets.system.{key}.enabled`

(`{key}` is the registry id, with no `Widget` suffix.)

**Option B — Nimbus trainhop**

1. Install [Nimbus devtools](https://github.com/mozilla-extensions/nimbus-devtools/releases/tag/release%2Fv0.3.0)
2. Choose "Feature configuration enrollment" on the left side
3. Opt into an experiment for `newtabTrainhop` with the entry's
   `trainhopEnabledKey` (e.g. `{key}Enabled`):

```json
{
  "type": "widgets",
  "payload": {
    "enabled": true,
    "{key}Enabled": true
  }
}
```
