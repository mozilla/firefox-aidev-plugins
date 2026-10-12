---
description: Scaffolds a new Firefox New Tab widget with a registry entry, JSX, SCSS, prefs, telemetry, the Customize panel toggle, and a draft test file. Use when the user wants to add a new widget to the New Tab page.
---

# New Tab Widget Scaffold

Widgets live in `browser/extensions/newtab/content-src/components/Widgets/{Name}/`.

Paths below are relative to `browser/extensions/newtab/` unless they start
with `browser/`; `Widgets/...` and `Nova/...` are under
`content-src/components/`. The **Widget Registry** (`common/WidgetsRegistry.mjs`) is the
single source of truth for every widget: you add one registry entry plus one
component-registry entry, and shared helpers (`isWidgetEnabled`,
`resolveWidgetSize`, `resolveWidgetHasSidebar`, `getHideAllTargets`,
`resolveWidgetOrder`), shared UI (`WidgetMenuButton`, `WidgetMenuFooter`,
`SizeSubmenu`, `MoveSubmenu`, `WidgetWrapper`) and the `useWidgetTelemetry`
hook do the rest. The Customize panel's "Manage widgets" subpanel is generated
from the registry too, and it is the only settings surface a widget has (Step 2
item 9). Do **not** hand-wire enabled-logic, size derivation, hide-all, the menu
button, the menu footer, the settings toggle, or telemetry payloads.

## Naming convention (read first)

The widget **id/key** and **telemetry name** must NOT contain the word
"widget". Use `widgets.example.enabled`, telemetry `"example"` — not
`widgets.exampleWidget.enabled` / `"example_widget"`. The telemetry name is
the snake_case form of the id (`readingList` gives `reading_list`); the
script derives it. See "Widget naming convention" in notes.md for why.

## Telemetry (do NOT touch metrics.yaml)

Widget telemetry is fully generic and already defined once for all widgets in
`browser/components/newtab/metrics.yaml`: `widgets_impression`,
`widgets_user_event`, `widgets_enabled` and `widgets_error` per widget, each
keyed by `widget_name` (your `telemetryName`) plus `widget_size`,
`error_type`, `user_action`, etc., and `widgets_container_action` for the
container itself.

A new widget therefore adds **nothing** to `metrics.yaml` and requires **no**
`./mach newtab channel-metrics-diff` run. It emits the shared events through the
`useWidgetTelemetry` hook (Step 2 item 3; see "Telemetry" in notes.md).
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
keys) and prints a widget spec, a `WIDGET_REGISTRY` entry to paste (with the
l10n ids, the customize-panel event source and the trainhop namespace derived
for you; fill in `order` yourself if the answer was `next`) and the list of
Fluent ids the widget needs, with placeholder values the copywriter replaces.
Wait for the user to paste that summary before proceeding.

### Step 2 — Plan

Enter plan mode. Using the spec and the example in
`references/ExampleWidget/`, propose the full list of files to create/modify
before writing anything. Read `references/notes.md` for non-obvious requirements
and gotchas.

The registry-centric core (do these first, in order):

1. `common/WidgetsRegistry.mjs` — append the `WIDGET_REGISTRY` entry (next
   `order` integer) and export the widget's pref-key constants
   (`PREF_WIDGETS_{KEY}_ENABLED`, `PREF_{KEY}_SIZE`,
   `PREF_WIDGETS_SYSTEM_{KEY}_ENABLED`). `isWidgetEnabled` derives everything
   from the entry. Keep the script's `customizeL10nId` and
   `customizeEventSource` (Jest fails without them) and
   `trainhopNamespace: "widget{Name}"` (without it a rollout through the
   widget's dedicated namespace does nothing). See "The Widget Registry is the
   source of truth" and "Trainhop namespaces" in notes.md. The shared tests in
   items 12 to 14 start failing as soon as this entry exists, so a TDD run
   sees them red at this point, not after the component.
2. `lib/ActivityStream.sys.mjs` — register the four prefs:
   `widgets.{key}.enabled`, `widgets.system.{key}.enabled`,
   `widgets.{key}.size` and `widgets.{key}.interaction`, plus any `extraPrefs`
   from the spec with their type and default. The page reads them from the
   Redux store, so an unregistered pref makes the widget silently not appear.
   - The two enabled prefs follow the "off everywhere" pattern every new widget
     starts with: `widgets.{key}.enabled`
     gets `getValue: () => !marketGateEnabled()` and
     `widgets.system.{key}.enabled` gets `value: false`, each with the comment
     the other widgets carry: `Off everywhere. To release organically: add
     locale-config to firefox.js, switch to marketGate.` Do not use
     `marketGate("...")` (release work, not scaffolding) or a literal `false`
     for the user pref; see "Market gating" in notes.md for why.
   - The size pref's `value` is `""`; see "Size: resolveWidgetSize and the
     empty-string sentinel" in notes.md.
   - The interaction pref is a boolean defaulting to `false`; `Widgets.jsx`
     flips it to `true` from `handleUserInteraction` only when the current value
     is strictly `false`, so without the registration the "New" badge never
     clears. It has no exported constant; the container builds the name from
     the id.
3. `Widgets/{Name}/{Name}.jsx` — the widget component. Mirror
   `references/ExampleWidget/ExampleWidget.jsx`, renaming `ExampleWidget` to
   the spec's `componentName` (`Horoscopes`, not `HoroscopesWidget`) and
   `example` to the css class:
   - Look up its entry once: `const ENTRY = WIDGET_REGISTRY.find(w => w.id === "{key}")`.
   - Derive size with `resolveWidgetSize(ENTRY, prefs)` — never read the size
     pref directly.
   - Destructure `dispatch`, `handleUserInteraction`, `widgetsMayBeMaximized`
     and `widgetEnabledMap`. Destructure `isMaximized` only when something
     reads it; do NOT pull it in and silence it with
     `eslint-disable-next-line no-unused-vars`. See "Standard widget props" in
     notes.md.
   - Emit telemetry through the `useWidgetTelemetry({ dispatch, widget: ENTRY,
     widgetSize })` hook, with `impressionRef` on the root element and
     `recordUserAction` for interactions, as the example does. See "Telemetry"
     in notes.md.
   - Render the shared `<WidgetMenuFooter>` as the last child of the menu's
     `<panel-list>`, with widget-specific items **above** it, and pass the
     Change size submenu through its `sizeSubmenu` prop as the example does
     (`null` when `widgetsMayBeMaximized` is false). Do **not** hand-roll the
     size submenu, `MoveSubmenu`, the Hide item, or the Learn more item, and
     do not dispatch `OPEN_LINK` from `onLearnMore`. Pass
     `showDivider={false}` while the widget has no items of its own above the
     footer; a blank scaffold is exactly that case. See "Context menu" in
     notes.md.
   - Render its own `<article className="{css} widget col-4 ${widgetSize}-widget">`
     root. Do **not** add a per-widget Nova gate; see "Nova gating is
     container-level, NOT per-widget" in notes.md.
   - The header is standard across widgets; copy it from the example: an
     `<h2>` (the container's section heading is an `<h1>`) whose id the
     `<article>`'s `aria-labelledby` names, so the title is the widget's
     accessible name (do not restyle it), the "New" `<moz-badge>` shown while
     `prefs["widgets.{key}.interaction"]` is false, and the shared
     `<WidgetMenuButton>` followed by the `<panel-list
     className="panel-list-no-icons">` (every widget menu carries that class).
     Do **not** write your own `<moz-button iconSrc=... menuId=...>`.
   - If the spec says view-only, delete the example's `DO_THING` action,
     `handleDoThing` and the body button; otherwise replace them with the
     spec's `userActions` and body.
   - If the spec has `hasSidebar: true`, read `references/SidebarVariant.md`
     before writing the component: the widget then takes `size` from props
     instead of calling `resolveWidgetSize`, and the sidebar has constraints
     that may rule the variant out.
4. `Widgets/WidgetsComponentRegistry.jsx` — add the component to
   `WIDGET_ROW_COMPONENTS`. If the spec has `hasSidebar: true`, also add a
   sidebar component to `WIDGET_SIDEBAR_COMPONENTS` — see
   `references/SidebarVariant.md` for that wiring.
5. `Widgets/Widgets.jsx` — add the widget's id to the hand-maintained
   `widgetEnabledMap` object (mirror the `clocks`/`privacy` entries):
   `{key}: isWidgetEnabled(WIDGET_REGISTRY.find(w => w.id === "{key}"), prefs, widgetsEnabled)`.
   **This map is the one hand-wired part of the container**, and a widget
   missing from it silently never renders; see "widgetEnabledMap in
   Widgets.jsx is hand-wired" in notes.md. No widget test catches a missing
   entry, so add a smoke test to `Widgets.test.jsx`: with `nova.enabled`,
   `widgets.enabled` and the widget's two enabled prefs on, the container
   renders `article.{css}.widget`.

The supporting files (each widget touches these):

6. `Widgets/{Name}/_{Name}.scss` — styles. `@include widget-base-style` on the
   root (NOT `newtab-card-style`): it provides the shared per-size card height,
   hover, transitions, and `position: relative`. Including `newtab-card-style`
   directly leaves the card with no height, so a sparse or not-yet-wired widget
   body collapses. Add `&.medium-widget { grid-row: span 2; }` and
   `&.large-widget { grid-row: span 4; }` inside the root class; add
   `&.small-widget { grid-row: span 1; }` only if `validSizes` includes `"small"`.
   The title's typography comes from the shared `.newtab-widget-title` rule in
   `Widgets/_Widgets.scss`, and the menu button from `WidgetMenuButton`, so the
   widget's own stylesheet lays out the title row (a flex wrapper), styles the
   "New" badge (the `.{css}-new-badge` block and its forced-colors override,
   copied from the example) and reveals the menu wrapper on hover, as the
   example does.
7. `content-src/styles/activity-stream.scss` — add `@import` of the widget SCSS.
   Do NOT also import it into `content-src/styles/nova/activity-stream.scss`.
8. Do NOT add the widget SCSS to the repo-root `stylelint-rollouts.config.js`.
   Write the SCSS design-token clean instead: `var(--space-*)`,
   `var(--font-*)`, `var(--border-radius-*)`, semantic colour tokens. If one
   declaration genuinely cannot use a token, put a targeted
   `stylelint-disable-next-line stylelint-plugin-mozilla/use-design-tokens` on
   that line, as Picture of the Day does. Do NOT add a file-level
   `/* stylelint-disable ... */`. See "SCSS @import (and NOT the stylelint
   rollout list)" in notes.md for items 7 and 8.
9. about:preferences (`about:preferences#home`, Firefox Home) — nothing to do.
   It does not list widgets, so a new widget needs no `home-prefs-*` string
   and no registry field for it. Do not copy Weather's standalone row there;
   see "about:preferences" in notes.md.
10. Customize panel — no code edit either. The Nova "Manage widgets" subpanel
   builds the toggle from the entry's `customizeL10nId` and
   `customizeEventSource` (item 1); add the toggle label to `newtab.ftl` as an
   attribute-only `.label` message, `newtab-custom-widget-{css-class}-toggle`,
   next to the other `newtab-custom-widget-*-toggle` strings.
   Leave the classic (Nova off) widget toggle block in
   `CustomizeMenu/ContentSection/ContentSection.jsx` alone, along with the
   `mayHave*Widget` props that `Base.jsx` and `CustomizeMenu.jsx` pass down for
   it, and leave the classic toggle out when copying Crossword or Recent
   Searches. See "Customize panel: generated from the registry" in notes.md.
11. `test/jest/content-src/components/Widgets/{Name}.test.jsx` — a dedicated Jest
    test file, started from `Horoscopes.test.jsx` in the same directory, the
    model widget test. Import `WrapWithProvider` from `test/jest/test-utils.jsx`
    (no local provider wrapper). The "Tests go in Jest" section of notes.md
    says what it has to cover.
12. `test/jest/content-src/components/Widgets/WidgetsRegistry.test.jsx` — three
    edits: append the new id to the hardcoded expected-order arrays in the
    `getWidgetOrder` and `resolveWidgetOrder` cases (registry order; several
    arrays in each describe); add the id and its
    `customizeEventSource` to the literal `EXPECTED_EVENT_SOURCES` map; and add
    an `isWidgetAddable` case, "is addable when revealed via the dedicated
    widget{Name} namespace", mirroring the existing ones.
13. `test/jest/content-src/components/Nova/CustomizeMenu/WidgetsManagementPanel/WidgetsManagementPanel.test.jsx`
    — the "Manage widgets" subpanel sorts by localised label and this test
    writes the expected orders out by hand, in several locales:
    - Add the new widget's label to every `*_LABELS` map: the en-US label,
      and in the German, Greek and Japanese maps a real word in that
      language and script (the shipped translation once it exists, a
      plausible one until then, never the English name). Add the widget to
      the comment above the maps that lists labels without translations.
    - Slot its id into each label-sorted `*_ORDER` array where
      `localeCompare` with no locale argument puts the label (the panel and
      Jest both use that default collation), working the position out by
      hand, never copying it from the test's output.
    - `ID_ORDER` (labels missing) sorts by registry id, and
      `TIMER_ID_SORT_ORDER` sorts Timer under its id and every other widget
      under its label.
    - Extend the `WIDGETS` fixture list.
    - Two inline expectations change when the new label sorts there: the
      array in "keeps a reduced set sorted when only some widgets are
      available", and the `indexOf("weather-toggle")` position in the Greek
      test if the new Greek label sorts before Weather.
    - `test/jest/content-src/components/DiscoveryStreamAdmin.test.jsx` sorts
      the devtools widget list the same way: add the label to its `labels`
      map, bump its `toHaveLength` count, and slot the id into its expected
      array.
    See "Customize panel: generated from the registry" in notes.md for why the
    labels must be in each locale's script.
14. `test/jest/content-src/components/Widgets/Widgets.test.jsx` — in the
    hide-all helper `expectAllWidgetPrefsDisabled`, bump the `toHaveLength(N)`
    count and add `PREF_WIDGETS_{KEY}_ENABLED` to its pref list (the file
    declares these constants locally near the top). See "hide-all is
    registry-derived" in notes.md.
15. `test/jest/lib/ActivityStream.test.js` — add `widgets.{key}.enabled` to
    the `USER_PREFS` list in the "market gating turned off" describe
    (`SYSTEM_PREFS` there holds only system prefs computed by `marketGate`, so
    the new one does not go in), and a `describe("{name} widget defaults")`
    asserting both enabled prefs are `false` after `_updateDynamicPrefs()`,
    mirroring the Horoscopes block. Both read `false` because the file's
    top-level `beforeEach` stubs `widgets.marketGate.enabled` to `true`, the
    shipped state. `test/jest/lib/PrefsFeed.test.js` has a three-row `it.each`
    block per widget for the trainhop shapes that turn a preffed-off widget
    on; copy the Horoscopes block and change the payload keys and the
    asserted pref.

Additional files only if the spec requires them:
- `common/Actions.mjs` + `common/Reducers.sys.mjs` — only if Redux state is
  needed. Keep new `WIDGETS_*` action types in alphabetical order with their
  neighbours; `test/jest/common/Actions.test.js` asserts the order. Model the
  reducer on `PrivacyWidget` (merge the update, set `initialized: true`) and
  add the slice to `INITIAL_STATE` and the `reducers` export.
- `lib/Widgets/{Name}Feed.sys.mjs` — only if the widget needs a backend data
  feed (see `lib/Widgets/RecentSearchesFeed.sys.mjs` for a small one). Its
  enabled check is `isWidgetEnabled(ENTRY, prefs, prefs?.["widgets.enabled"])`
  with the entry looked up from `WIDGET_REGISTRY`, as the Recent Searches,
  Privacy and Picture of the Day feeds do, so the feed also stops when the
  user hides all widgets; do not read the system pref or
  `trainhopConfig.widgets.*` by hand. A feed that reacts to enablement
  changes lists `widgets.enabled`, the enabled pref, the system pref and
  `trainhopConfig` among the `PREF_CHANGED` names it watches, as Recent
  Searches does. Four edits go with it:
  1. `lib/ActivityStream.sys.mjs`: a lazy getter in the
     `ChromeUtils.defineESModuleGetters(lazy, {...})` block
     (`{Name}Feed: "resource://newtab/lib/Widgets/{Name}Feed.sys.mjs"`) and an
     entry in `FEEDS_DATA` (`{ name: "{keylowercase}feed", factory: () => new
     lazy.{Name}Feed(), title: "...", value: true }`; feed names are all
     lower case, `recentsearchesfeed`), which registers the
     `feeds.{keylowercase}feed` pref that turns the feed on.
  2. `test/xpcshell/test_{Name}Feed.js`, listed alphabetically in
     `test/xpcshell/xpcshell.toml`.
  3. The store declaration every feed carries:
     `/** @import {Store} from "resource://newtab/lib/Store.sys.mjs" */` at the
     top and a `/** @type {Store} */ store = null;` class field. Keep the JSDoc
     accurate; see "Feeds are type-checked" in notes.md.
  4. Any Redux slice the feed broadcasts to (`Actions.mjs`, `Reducers.sys.mjs`,
     and the reducer test described in "Tests go in Jest" in notes.md).

### Step 3 — Scaffold

After plan approval, implement all files end-to-end without stopping between
edits. Do not pause to summarize progress or ask for confirmation mid-scaffold.
Work through every file in the plan in sequence, replicating the patterns in
`references/ExampleWidget/` and substituting values from the spec. The
example's explanatory comments are instructions to you: do not copy them into
the new widget (the repo keeps code comments to a minimum), but keep the
licence header in both files and the `eslint-disable-next-line` above the
React import, which every widget carries. Replace or delete the placeholder
body. Add every Fluent message the component references to
`newtab.ftl` in the same pass, with the script's placeholder values where the
copywriter's text has not arrived; an id without a message renders empty with
no error.

Only stop if you hit a genuine blocker (e.g. a file doesn't exist where expected,
or the codebase structure differs from what the plan assumed). In that case,
explain what you found and what decision is needed before continuing.

### Step 4 — Build and verify

After scaffolding, run lint with fixes first, since it can rewrite files:

```
./mach lint --fix <the files you touched>
```

Then build so the page shows the change (see "Building" in notes.md for how
the build generates the bundles and CSS):

1. `./mach build faster` — rebuilds the bundles and copies them to the build
   output. `./mach newtab bundle` is only a fallback if the page shows stale
   output.
2. A full `./mach build` once if Fluent strings were added: `build faster`
   skips locale processing, so new ids show as missing until then.

Then run the suite once. Most of the failures this skill warns about (hide-all
counts, registry order arrays, the hand-written label orders, an unresolved
Fluent id, a stylelint token violation) are invisible to the build:

```
./mach npm test --prefix=browser/extensions/newtab
```

`npm test` runs lint (codespell, eslint, the l10n check, license headers,
stylelint) and the whole Jest suite. Run it once before claiming the scaffold
is done, rather than repeating focused Jest passes. `./mach lint` on the touched
files adds the TypeScript check for anything under `lib/`. If a new feed was
added, also run its xpcshell test — and note a **new** `.sys.mjs` needs
`./mach build faster` before xpcshell can resolve it, or the test fails with a
bare `CRASH` and no stack.

Nothing above checks that the Fluent ids in the JSX exist: the l10n lint parses
the FTL file, and the Jest tests only compare attribute strings. An unresolved
id renders an empty element with no error. So list the ids the component uses
and confirm each one is defined, from the Firefox root:

```
rg -o 'newtab-{css-class}-[a-z-]+' browser/extensions/newtab/content-src/components/Widgets/{Name}/{Name}.jsx
rg -n '^newtab-{css-class}-' browser/locales/en-US/browser/newtab/newtab.ftl
rg -n '^newtab-custom-widget-{css-class}-toggle' browser/locales/en-US/browser/newtab/newtab.ftl
```

Every id from the first command must appear in the second (run the first on
every component file you created), and the third must find the Customize
toggle label, whose id the first pattern does not match. If some of the
widget's strings are already in `newtab.ftl` ahead of the component, check
their shape as well as their existence: a menu-button message without
`.title` is replaced by a new `newtab-{css-class}-widget-open-menu-button` id,
not edited in place (see "FTL file locations and string formats" in notes.md).

### Step 5 — Follow-up

**Always output this section in full after Step 4 — do not skip or summarize it.**

Tell the user which Fluent messages carry placeholder values for the
copywriter to replace (the four the scaffold always adds, plus any body and
menu strings), then output the full enable instructions below:

**Option A — `about:config`**

Set **all three** of these to `true`:
- `browser.newtabpage.activity-stream.widgets.system.enabled` (the parent switch for all widgets; on by default outside the regions in `widgets.system.region-block`, so usually already `true`)
- `browser.newtabpage.activity-stream.widgets.{key}.enabled`
- `browser.newtabpage.activity-stream.widgets.system.{key}.enabled`

(`{key}` is the registry id, with no `Widget` suffix.) A fourth pref,
`browser.newtabpage.activity-stream.widgets.enabled`, is the user's "hide all
widgets" switch; it defaults to `true` and `isWidgetEnabled` requires it, so
check it has not been turned off in the profile you test with. Market gating
is on, so the gated widgets' defaults are computed per region and locale (see
"Market gating" in notes.md); a value set in `about:config` still wins.

**Option B — Nimbus trainhop**

1. Install [Nimbus devtools](https://github.com/mozilla-extensions/nimbus-devtools/releases/tag/release%2Fv0.3.0)
2. Choose "Feature configuration enrollment" on the left side
3. Opt into `newtabTrainhop` with a multi-payload: one part reveals the
   widgets container, the other is the widget's own dedicated namespace
   (`trainhopNamespace`, `widget{Name}`), the shape every widget is rolled out
   with:

```json
{
  "type": "multi-payload",
  "payload": [
    { "type": "widgets", "payload": { "enabled": true } },
    { "type": "widget{Name}", "payload": { "visible": true, "enabled": true } }
  ]
}
```

`visible` reveals the widget and its toggles without writing a pref; `enabled`
sets the default of `widgets.{key}.enabled` (a user's own toggle still wins).
The per-key form, `{ "type": "widgets", "payload": { "enabled": true,
"{key}Enabled": true } }`, also works, but the dedicated form above is the one
rollouts use, and it needs the entry's `trainhopNamespace`.
