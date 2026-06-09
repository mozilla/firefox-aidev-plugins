# Widget Scaffolding Notes

Things that are non-obvious from the ExampleWidget alone. Only update this file
when a gotcha changes — if the example shows it clearly, it doesn't belong here.

## Widget naming convention — no "widget" suffix

The widget **id/key** and **telemetry name** must NOT contain the word "widget".
They already live under the `widgets.` pref namespace, so a `*Widget` suffix is
redundant. Model the naming on Weather:

- id `weather` → `widgets.weather.enabled`, `widgets.weather.size`,
  `widgets.system.weather.enabled`, trainhop `weatherEnabled`, telemetry `"weather"`.

The Sports widget got this wrong: it shipped as id `sportsWidget`
(`widgets.sportsWidget.enabled`, trainhop `sportsWidgetEnabled`) and it caused a
pref + telemetry bug that had to be fixed — its `telemetryName` is `"sports"`,
NOT `"sports_widget"`. Treat the Sports `*Widget` naming as legacy. New widgets
use the clean form (e.g. id `example`, telemetry `"example"`).

## The Widget Registry is the source of truth

`common/WidgetsRegistry.mjs` defines `WIDGET_REGISTRY` — one entry per widget —
and the helpers that derive everything else. You no longer hand-wire enabled
logic, size derivation, hide-all, or the null-guard into `Widgets.jsx` or
`Base.jsx`. Adding a widget is mostly: add a registry entry + a
`WIDGET_ROW_COMPONENTS` entry + register the prefs.

Each entry's fields: `id`, `telemetryName`, `order`, `enabledPref`, `sizePref`,
`defaultSize`, `validSizes`, `hasSidebar`, `systemEnabledPref`,
`trainhopEnabledKey`, `trainhopSizeKey`, `trainhopSidebarKey`. Export the pref-key
constants from this same file and register them in `ActivityStream.sys.mjs`.

The helpers (use these; do not reimplement the logic in components):

- `isWidgetEnabled(entry, prefs, widgetsEnabled)` — whether the widget is on.
- `isWidgetAddable(entry, prefs)` — the system/trainhop gate, ignoring the user toggle.
- `resolveWidgetSize(entry, prefs)` — the effective size (see below).
- `resolveWidgetHasSidebar(entry, prefs)` — sidebar placement (trainhop override
  then static flag).
- `getHideAllTargets(prefs, widgetEnabledMap)` — the list "hide all" disables.
- `resolveWidgetOrder(prefs)` / `getWidgetOrder(orderPref)` — render order.

The registry's own top doc-comment is the canonical "ADDING A NEW WIDGET" recipe —
read it before scaffolding.

## Nova gating is container-level, NOT per-widget

`nova.enabled` still defaults to `false` and `Widgets.jsx` keeps a dual render
path: `if (novaEnabled) { …render WIDGET_ROW_COMPONENTS… } else { …legacy… }`.
A new widget is registered only in `WIDGET_ROW_COMPONENTS`, so it mounts **only**
in the Nova branch. That means the container already gates it on Nova — do **not**
add a per-widget `if (!prefs[PREF_NOVA_ENABLED]) return null;` or a
`@nova-cleanup(remove-gate)` comment to a new widget.

SportsWidget *does* have a per-widget Nova gate; that is legacy and must not be
copied. (Older widgets like FocusTimer/Lists also carry conditional Nova logic
because they predate the registry — new widgets don't need any of it.)

## Size: resolveWidgetSize and the empty-string sentinel

`resolveWidgetSize(entry, prefs)` applies priority:
1. user-set `sizePref` (non-empty) — always wins
2. `trainhopConfig.widgets[trainhopSizeKey]` — a default suggestion, not an override
3. `entry.defaultSize` — final fallback

The size pref's `value` in `PREFS_CONFIG` is `""` (empty string). Empty means
"the user has not chosen a size", which is what lets the trainhop suggestion and
`defaultSize` apply. Once the user resizes, the pref holds a real value and wins.
Never read the size pref directly in a component — go through `resolveWidgetSize`.

(Weather is the one exception: its size pref uses `getValue: getWeatherWidgetSize`
in `ActivityStream.sys.mjs` for a one-time migration from the old weather config.)

## Build order matters

Register the prefs in `ActivityStream.sys.mjs` **first**, then run
`./mach build faster` before scaffolding the rest. The container reads prefs from
the Redux store — if they aren't registered by the build yet, the widget won't
appear even when Nimbus/trainhop is configured.

## `./mach newtab bundle` is required for SCSS/JSX changes

`./mach build faster` only copies already-compiled files to the build output. It
does **not** recompile SCSS or JS. After any SCSS or JSX change:

1. `./mach newtab bundle` — compile
2. `./mach build faster` — copy to the build output
3. Reload `about:newtab`

The compiled artifacts (`css/activity-stream.css`, `css/nova/activity-stream.css`,
`data/content/activity-stream.bundle.js`) are checked into the repo and must be
committed after bundling.

## SCSS @import and the stylelint rollout list

Add the widget's `_{Name}.scss` `@import` to
`content-src/styles/activity-stream.scss`. (`styles/nova/activity-stream.scss`
still exists for the CSS-switcher path but the main entry point is what matters
for new widgets.) Then add the SCSS file path to `stylelint-rollouts.config.js`
at the repo root, in alphabetical order alongside the other widget entries.

Nova-specific CSS must be scoped under `.nova-enabled`.

## `widgets.system.enabled` is the parent gate

The entire widgets section (customize panel, about:preferences, and the widget
container) is gated by `widgets.system.enabled`, which defaults to `false`. Even
with all per-widget prefs set, nothing appears unless this parent gate is enabled
via `about:config` or a Nimbus experiment. Always include it in enable instructions.

## Customize panel toggle (Base.jsx + CustomizeMenu + WidgetsManagementPanel)

The toggle in the customize panel requires edits in a chain — miss one and the
toggle silently never appears:

1. `Base.jsx` — compute `mayHave{Name}Widget` (mirror an existing widget such as
   `mayHaveListsWidget`) and pass it to **both** `<CustomizeMenu>` renders.
   `Base.jsx` renders `<CustomizeMenu>` in two places (different layout modes) —
   search for `mayHaveListsWidget={` to find both.
2. `content-src/components/CustomizeMenu/CustomizeMenu.jsx` — forward the prop
   (required passthrough).
3. `content-src/components/Nova/CustomizeMenu/WidgetsManagementPanel/WidgetsManagementPanel.jsx`
   — add a `moz-toggle` block. This is now a functional component; mirror an
   existing widget's section (it sets `data-preference="widgets.{key}.enabled"`,
   `data-event-source`, and `data-l10n-id`).
4. `ContentSection.jsx` — the classic-layout path.
5. `browser/locales/en-US/browser/newtab/newtab.ftl` — the toggle label
   (`newtab-custom-widget-{css-class}-toggle`).

When in doubt, grep an existing widget's key (e.g. `lists`, `weather`) across
these files and replicate every hit.

## about:preferences registration

Register the widget in `lib/AboutPreferences.sys.mjs` so it appears under
`about:preferences#home`, and add a `home-prefs-{css-class}-header` string to
`browser/locales/en-US/browser/preferences/preferences.ftl`. The exact shape of
the entries in this file evolves — mirror an existing widget (weather or lists)
rather than copying a fixed snippet.

## FTL file locations and string formats

Widget strings live in two FTL files:

- `browser/locales/en-US/browser/newtab/newtab.ftl` — new tab page strings
  (the bundled copy lives under `webext-glue/locales/...`, but author in the
  source `browser/locales/...` file)
- `browser/locales/en-US/browser/preferences/preferences.ftl` — about:preferences

Shared strings already exist — reuse them, do not redefine:
`newtab-widget-menu-hide`, `newtab-widget-menu-change-size`,
`newtab-widget-menu-move`, `newtab-widget-menu-move-left`,
`newtab-widget-menu-move-right`, `newtab-widget-size-small`/`-medium`/`-large`.

String formats differ by type — do not mix them up:

**Customize panel toggle** — uses `.label`:
```ftl
newtab-custom-widget-{css-class}-toggle =
    .label = {Display Name}
```

**about:preferences header** — uses `.label`:
```ftl
home-prefs-{css-class}-header =
    .label = {Display Name}
```

**Context menu Learn More** — plain string:
```ftl
newtab-{css-class}-menu-learn-more = Learn more
```

Add a `##` group comment only at the start of a section, never trailing. A `##`
with no messages after it is a lint error (GC04).

Never invent user-facing string values — copy comes from a copywriter. Wait for
the literal text before adding the message.

## Widget resize context menu — use the useSizeSubmenu hook

The resize submenu is a `<panel-item submenu>` containing a `<panel-list>` of
size `<panel-item type="checkbox">` rows. Wire its clicks with the shared
`useSizeSubmenu(handleChangeSize)` hook from `content-src/lib/utils`:

```jsx
const sizeSubmenuRef = useSizeSubmenu(handleChangeSize);
// ...
<panel-list ref={sizeSubmenuRef} slot="submenu" id="{css-class}-size-submenu">
```

Do NOT hand-roll a `useEffect` + `composedPath()` click listener — that's exactly
what the hook now encapsulates. React's synthetic `onClick` does not cross the
`panel-list` shadow-DOM boundary, which is why the hook listens at the root.

Gate the submenu on `widgetsMayBeMaximized`. Build the size list from the entry's
`validSizes` — include `"small"` only when it is present.

## Widget reorder — the MoveSubmenu component

Widgets can be reordered. Render the shared component in the context menu, before
Hide/Learn more:

```jsx
import { MoveSubmenu } from "../MoveSubmenu";
// ...
<MoveSubmenu widgetId="{key}" widgetEnabledMap={widgetEnabledMap} />
```

It reads/writes the `widgets.order` pref via `resolveWidgetOrder`, renders nothing
when the widget can't move, and (like the size submenu) listens at the panel-list
root for `data-move-dir` clicks. You don't write any order logic yourself.

## Standard widget props

Row widgets receive: `dispatch`, `handleUserInteraction`, `isMaximized`,
`widgetsMayBeMaximized`, and `widgetEnabledMap` (a map of `id → boolean` for which
widgets are currently active — used by `MoveSubmenu` and any cross-widget checks).
A widget that takes its size from a row-wrapper (see sidebar variant) also receives
a `size` prop. Omit `handleUserInteraction` for view-only widgets.

## WidgetWrapper is a container concern

`Widgets/WidgetWrapper.jsx` applies `widget-wrapper col-4` and drag-and-drop
plumbing. The container wraps widgets with it — the widget component renders its
own `<article className="{css} widget col-4 ${size}-widget">` and does not import
WidgetWrapper itself.

## Trainhop key namespace

Trainhop overrides are read from `trainhopConfig.widgets.*` using the keys named
in the registry entry: `trainhopEnabledKey`, `trainhopSizeKey`, and
`trainhopSidebarKey`. The convention is camelCase id + suffix
(`{key}Enabled`, `{key}Size`, `{key}Sidebar`). The registry helpers already read
these — you only declare the keys on the entry.

## Sidebar variant (optional)

Widgets can render in the sidebar at size `"small"` via `hasSidebar: true` plus a
component in `WIDGET_SIDEBAR_COMPONENTS` (Weather is the only one today). This is
not part of the default scaffold. When a spec needs it, see
[`SidebarVariant.md`](./SidebarVariant.md) for the registry fields and the
row-wrapper / sidebar-component split.

## hide-all is registry-derived

"Hide all widgets" is driven by `getHideAllTargets(prefs, widgetEnabledMap)` and
the `WIDGETS_HIDE_ALL` action — you do not edit a hand-maintained list of
`SetPref` dispatches anymore. Adding a registry entry automatically includes the
widget. (The legacy per-widget `hideAllWidgets` test-count assertions no longer
apply.)

## Action types must be alphabetically sorted

The action types in `common/Actions.mjs` are alphabetically sorted, and a test in
`test/unit/common/Actions.test.js` asserts it. Only relevant if your widget needs
new `WIDGETS_*` action types (most don't). Keep them in order, e.g.
`WIDGETS_..._SEEN` before `WIDGETS_..._SET`.

## batch() on every multi-dispatch

Any handler that dispatches two or more actions must wrap them in `batch()` to
avoid intermediate renders — hide handlers, resize, user events that pair a state
change with a telemetry dispatch, etc.

## Learn More URL

Always point to `https://support.mozilla.org/kb/firefox-new-tab-widgets`. Do not
create a widget-specific SUMO page — all widgets share this URL.

## Use the `.jsx` extension for content-src files

Files in `content-src/` must use `.jsx`, not `.js`. The ESLint config only treats
`test/**/*.js` as ES modules; a `.js` file in `content-src/` fails with
`Parsing error: 'import' and 'export' may appear only with 'sourceType: module'`.

## Redux state (optional)

Only add a Redux slice if the widget needs cross-tab persistence or complex shared
state. Simple local state (`useState`) is preferable for transient UI. When in
doubt, don't add Redux — it can be added later.

## Tests go in Jest

New per-widget tests live in `test/jest/content-src/components/Widgets/{Name}.test.jsx`
(React Testing Library + `expect()`), alongside `SportsWidget.test.jsx`,
`Weather.test.jsx`, etc. There is also a `WidgetsRegistry.test.jsx` for
registry-level coverage. The legacy `test/unit/` Enzyme suite still exists, but
add new tests to Jest unless extending an existing Enzyme file.
