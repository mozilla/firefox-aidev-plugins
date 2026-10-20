# Widget Scaffolding Notes

Things that are non-obvious from the ExampleWidget alone. Only update this file
when a gotcha changes — if the example shows it clearly, it doesn't belong here.

## Widget naming convention

The id and telemetry name carry no "widget" (SKILL.md "Naming convention (read first)")
because they already live under the `widgets.` pref namespace, so a `*Widget`
suffix is redundant. Model the naming on Weather:

- id `weather` → `widgets.weather.enabled`, `widgets.weather.size`,
  `widgets.system.weather.enabled`, trainhop `weatherEnabled`, telemetry `"weather"`.

A suffixed id (`exampleWidget`, trainhop `exampleWidgetEnabled`) drifts from
the telemetry name, which is always the clean form (`"example"`, never
`"example_widget"`), so use the clean form everywhere.

## The Widget Registry is the source of truth

`common/WidgetsRegistry.mjs` defines `WIDGET_REGISTRY` — one entry per widget —
and the helpers that derive everything else. You do not hand-wire enabled
logic, size derivation, hide-all, or the null-guard into `Widgets.jsx` or
`Base.jsx`. Adding a widget is mostly: add a registry entry + a
`WIDGET_ROW_COMPONENTS` entry + register the prefs.

Each entry's fields: `id`, `telemetryName`, `customizeL10nId`,
`customizeEventSource`, `order`, `enabledPref`, `sizePref`, `defaultSize`,
`validSizes`, `hasSidebar`, `systemEnabledPref`, `trainhopEnabledKey`,
`trainhopSizeKey`, `trainhopSidebarKey`, `widgetsSettingsVisibleKey`,
`widgetsSettingsEnabledKey`, `trainhopNamespace`. The pref-key constants are
exported from this same file and registered in `ActivityStream.sys.mjs`
(SKILL.md Step 2 items 1 and 2).

Two fields feed the generated Customize panel toggle: `customizeL10nId` labels
it, and `customizeEventSource` (`WIDGET_` plus the upper-case telemetry name,
e.g. `WIDGET_PICTURE_OF_THE_DAY`) is the `PREF_CHANGED` telemetry source the
toggle sends, so pick it once. `WidgetsRegistry.test.jsx` requires both on
every non-retired entry and checks the event source against a literal map
(SKILL.md Step 2 item 12). There is no about:preferences field; see
"about:preferences" below.

The two `widgetsSettings*` keys are easy to miss and every current entry has
them: `*VisibleKey` additively reveals the widget's toggle in the settings UIs,
and `*EnabledKey` overrides the enabled pref's default value. Omit them and the
toggle misbehaves under a trainhop rollout. `trainhopNamespace` is just as easy
to miss and matters more: it names the object a Nimbus rollout ships the
widget's config in (see "Trainhop namespaces" below). Optional fields some
entries carry: `requiresHistory` (hide the widget on profiles that record no
history), `requiresWidgetSearchSap` (the same idea for a platform dependency),
`skipNightlyDefault` (keep the widget off on Nightly too under market gating),
and `retired`.

**Appending the entry matters more than the `order` number.** Default ordering
follows the array position, not a numeric sort of `order`, so add the entry last
and give it the next integer. A `retired: true` entry keeps its position while
its code is removed, so count array positions, not rendered widgets.

The helpers (use these; do not reimplement the logic in components):

- `isWidgetEnabled(entry, prefs, widgetsEnabled)` — whether the widget is on.
- `isWidgetAddable(entry, prefs)` — whether the system pref or a trainhop payload
  reveals the widget, ignoring the user toggle.
- `resolveWidgetSize(entry, prefs)` — the effective size (see below).
- `resolveWidgetHasSidebar(entry, prefs)` — sidebar placement (trainhop override
  then static flag).
- `getHideAllTargets(prefs, widgetEnabledMap)` — the list "hide all" disables.
- `resolveWidgetOrder(prefs)` / `getWidgetOrder(orderPref)` — render order.

The registry's own top doc-comment has an "ADDING A NEW WIDGET" recipe. Read
it first for the tree's own view of the steps, then follow this skill for
everything the comment leaves out: it names two prefs where four are
registered, does not mention `trainhopNamespace` (a widget without one
cannot be rolled out through its own Nimbus namespace), and lists no test
files or Fluent ids. If the comment ever describes a surface differently from
this skill, the tree has moved and the skill needs updating; say so rather
than guessing.

## Nova gating is container-level, NOT per-widget

`nova.enabled` ships on (`firefox.js` sets it to `true`; the extension's own
fallback is `false`), and `Widgets.jsx` keeps a dual render path: `if (novaEnabled) { …render WIDGET_ROW_COMPONENTS… } else { …legacy… }`.
A new widget is registered only in `WIDGET_ROW_COMPONENTS`, so it mounts **only**
in the Nova branch. That means the container already gates it on Nova — do **not**
add a per-widget `if (!prefs[PREF_NOVA_ENABLED]) return null;` or a
`@nova-cleanup(remove-gate)` comment to a new widget.

Lists, Focus Timer and Weather carry conditional Nova logic because they also
render with Nova off; a new widget needs none of it.

## widgetEnabledMap in Widgets.jsx is hand-wired

`Widgets.jsx` builds a literal `widgetEnabledMap` object by hand, the one
exception to "do not hand-wire enabled-logic into `Widgets.jsx`". The render
loop checks `widgetEnabledMap[id]`, so a widget that is missing from this map
**silently never renders** even when its registry entry, `WIDGET_ROW_COMPONENTS`
entry, and prefs are all correct — and `about:newtab` shows nothing with no
error. This is the most common "I scaffolded a widget and it doesn't appear"
cause. SKILL.md Step 2 item 5 has the entry to add.

## Size: resolveWidgetSize and the empty-string sentinel

`resolveWidgetSize(entry, prefs)` applies priority:
1. user-set `sizePref` (non-empty) — always wins
2. `trainhopConfig.{trainhopNamespace}.size` — the dedicated namespace's suggestion
3. `trainhopConfig.widgets[trainhopSizeKey]` — the shared-key suggestion
4. `entry.defaultSize` — final fallback

The size pref's `value` in `PREFS_CONFIG` is `""` (empty string). Empty means
"the user has not chosen a size", which is what lets the trainhop suggestion and
`defaultSize` apply. Once the user resizes, the pref holds a real value and wins.
One override runs before all four: while the first-content-slot experiment is
active, the widget selected for that slot is forced to `large`
(`selectFirstSlotWidget`, at the top of `resolveWidgetSize`).

(Weather is the one exception: its size pref uses `getValue: getWeatherWidgetSize`
in `ActivityStream.sys.mjs` for a one-time migration from the old weather config.)

## Building

The build generates the bundles and CSS itself: `moz.build` runs
`build-newtab-bundles.py` when Node is configured, and it hashes every `.jsx`,
`.mjs` and `.scss` under `content-src/` and `common/`, so `./mach build faster`
rebuilds them after any change (SKILL.md Step 4 has the commands). The outputs
land in the object directory and are never part of the patch, which carries
the hand-written files (sources, registry, prefs, strings, tests).

## SCSS @import (and NOT the stylelint rollout list)

Why not the Nova stylesheet: `styles/nova/activity-stream.scss` imports only
Lists, Focus Timer, Weather and Clocks, so it is easy to assume new ones belong
there too. Every other widget is imported by the main stylesheet alone.

Why not the rollout list: the repo-root `stylelint-rollouts.config.js` grandfathers *existing*
files only, and its own header says so ("newly added style files should NOT be
added to this list"). Adding yours silently opts it out of `use-design-tokens`.

On disables: a file-level `/* stylelint-disable ... */` (Privacy) silently turns
the check off for the whole stylesheet. A targeted
`stylelint-disable-next-line` (Picture of the Day) turns it off for one
declaration you have justified. Prefer the second, and only where a token
genuinely does not exist.

**Verify every `var(--*)` you add actually resolves.** Invented but
plausible-sounding token names are a recurring failure mode, and
`var(--name, fallback)` renders the fallback so manual testing never catches it.
For each new token, from the Firefox root, scoped to the two places tokens are
defined (the repo guidelines say not to run `rg` over the whole tree):

```
rg --fixed-strings -- "--your-token-name:" toolkit/themes/shared/design-system/dist browser/extensions/newtab/content-src/styles
```

A hit in `tokens-shared.css`, `_variables.scss` or a `:root` block is proof it
exists. No hit means you invented it. Custom properties that a component
element exposes for styling are a different thing: the `--badge-*` properties
the example's badge block sets are read by `moz-badge` itself, so check those
against the element's own stylesheet under `toolkit/content/widgets/`, not the
token files.

The newtab AGENTS.md rule that Nova-only CSS is scoped under `.nova-enabled`
is for components that also render with Nova off. Lists, Weather and Clocks
scope their Nova rules that way; every other widget stylesheet is unscoped,
because a registry widget renders only in the Nova branch of `Widgets.jsx`, so
the class is always present and adds nothing. Follow those and the example: no
`.nova-enabled` wrapper in the new stylesheet.

## `widgets.system.enabled` is the parent switch

The entire widgets section (the Customize panel's widgets section, the Widgets
row in about:preferences, and the widget container) depends on
`widgets.system.enabled`. Its default comes from `marketGate` (see below): on
everywhere, since the `widgets.system.region-block` list in `firefox.js`
is empty, and off if gating is ever switched off. A profile can still have it
off, so enable instructions always list it.

## Market gating

`ActivityStream.sys.mjs` computes the default of every widget `enabled` and
`system.enabled` pref with `marketGate(prefKey)`, driven by
`widgets.marketGate.enabled` (on by default) and by region and locale lists in
`browser/app/profile/firefox.js` named after the pref:
`widgets.system.{key}.region-block`, `widgets.{key}.region-block`,
`widgets.system.{key}.locale-config` and so on. An empty list means no
restriction, a block list wins over an allow list, and Nightly gets every widget
everywhere unless `widgets.marketGate.enforceOnNightly` is set or the entry
carries `skipNightlyDefault`. With gating switched off, `marketGate` returns
its pre-gating defaults: `true` for user prefs, `false` for system prefs.

A new widget does not take part in that. It starts "off everywhere" (SKILL.md
Step 2 item 2 has the two pref definitions and their comment). With gating on,
both are `false` on every channel (the expression
does not consult the Nightly rule); if gating is switched off, the user pref
goes back to `true` with every other widget's, which a literal `false` would
not do. Nimbus reveals and enables the widget through its trainhop namespace
in the meantime: `visible` makes it addable, `enabled` sets the user pref's
default (`PrefsFeed` writes it only when the payload sends it), and
`isWidgetEnabled` needs the container flag, `isWidgetAddable` and the user
pref all true. Releasing it organically later means adding its lists to
`firefox.js`, switching both prefs to `marketGate("...")`, and mirroring any
new list in `MARKET_PREF_FALLBACKS` (a `@backward-compat` stub for
train-hopped builds on a Firefox that lacks the pref).
`test/jest/lib/ActivityStream.test.js` has a defaults block per widget; add
one (SKILL.md Step 2 item 15).

## Customize panel: generated from the registry

The "Manage widgets" subpanel of the Nova customize panel
(`content-src/components/Nova/CustomizeMenu/WidgetsManagementPanel/WidgetsManagementPanel.jsx`)
maps every non-retired registry entry to a `moz-toggle`, keeps the ones
`isWidgetToggleVisible` allows, sorts them by their localised label
(`useWidgetLabels`), and on a flip sends `PREF_CHANGED` with the entry's
`customizeEventSource` plus `widgets_enabled` with its `telemetryName` and
resolved size. A new widget therefore needs no edit to the panel, to `Base.jsx`
or to `CustomizeMenu.jsx` (SKILL.md Step 2 item 10).

The classic (Nova off) customize menu in
`content-src/components/CustomizeMenu/ContentSection/ContentSection.jsx` lists
widgets by hand, with `mayHave*Widget` props threaded from `Base.jsx` through
`CustomizeMenu.jsx`. That block only matters when Nova is off, where a registry
widget cannot render (the container renders `WIDGET_ROW_COMPONENTS` only in its
Nova branch), so a classic toggle would switch a widget the classic page cannot
show. Crossword and Recent Searches have a classic toggle too (SKILL.md Step 2
item 10).

Because the panel sorts by label, its test (`WidgetsManagementPanel.test.jsx`)
keeps per-locale label maps and hand-written expected orders, and the devtools
widget list test (`DiscoveryStreamAdmin.test.jsx`) has one more; SKILL.md
Step 2 item 13 lists the edits. The non-English maps need labels in their own
language and script: a Latin stand-in in the Greek or Japanese map sorts
wherever the default collation puts Latin, so the hand-written order stops
testing anything about that locale.

## about:preferences

`about:preferences#home` does not list widgets. Its Widgets row holds one
"Manage widgets" link (`manageWidgets`, a `moz-box-link` to
`about:home#customize-widgets`), and `Base.jsx` opens the Customize panel on the
"Manage widgets" subpanel for that hash. `lib/AboutPreferences.sys.mjs`
registers no per-widget prefs or settings, so a new widget adds nothing there
and gets no `home-prefs-*` string.

Weather is the one exception. `AboutPreferences.sys.mjs` keeps a standalone
row for it with Nova off, and with Nova on while the widgets container is
hidden, under the literal id
`home-prefs-weather-header-srd`, with its system pref registered by hand under
its `trainhopEnabledKey`. That is specific to Weather, not a pattern; do not
copy it for a new widget.

## FTL file locations and string formats

Widget strings live in `browser/locales/en-US/browser/newtab/newtab.ftl`, the
New Tab page strings and the Customize panel toggle label alike. The bundled
copy lives under `webext-glue/locales/...`, but author in the source
`browser/locales/...` file. Do NOT use
`browser/locales/en-US/browser/preferences/preferences.ftl` for widget strings,
and do not add a `home-prefs-*` string (see "about:preferences").

Shared strings already exist — reuse them, do not redefine:
`newtab-widget-menu-hide`, `newtab-widget-menu-change-size`,
`newtab-widget-menu-move`, `newtab-widget-menu-move-left`,
`newtab-widget-menu-move-right`, `newtab-widget-size-small`/`-medium`/`-large`.
The "New" badge also reuses `newtab-widget-lists-label-new` — the other widgets
share it already, so do not add a per-widget copy.

Every widget has a **title** string, read by the shared title element and used
as the widget's accessible name:

```ftl
# Widget heading; also the widget's accessible name.
newtab-{css-class}-widget-title = {Display Name}
```

**The context-menu button needs its own string.** `WidgetMenuButton` is
icon-only, so without one a screen reader announces "button" with no indication
of what it opens. The standard message sets both attributes to the same text,
as every widget does:

```ftl
# Tooltip and screen reader label for the icon-only button that opens the
# widget's menu.
newtab-{css-class}-widget-open-menu-button =
    .title = Open {display name} menu
    .aria-label = Open {display name} menu
```

If some of the widget's strings are already in `newtab.ftl` ahead of its code,
check their shape before reusing them. A menu-button message that carries only
`.aria-label`, or an id such as `newtab-{css-class}-widget-menu-button`,
cannot gain `.title` in place: adding or removing an attribute changes the
message's morphology,
and the Fluent review guidelines require a new id for that. Add
`newtab-{css-class}-widget-open-menu-button` with both attributes and drop the
old message if nothing else uses it.

String formats differ by type — do not mix them up:

**Customize panel toggle** — uses `.label`:
```ftl
newtab-custom-widget-{css-class}-toggle =
    .label = {Display Name}
```
The `{css-class}` formula is a convention; existing ids vary
(`newtab-custom-widget-picture-toggle`, `newtab-custom-widget-search-toggle`).
Any id works as long as `customizeL10nId` and the FTL agree.

**Context menu Learn More** — plain string:
```ftl
# Context menu item linking to more information about the widget.
newtab-{css-class}-menu-learn-more = Learn more
```

Add a `##` group comment only at the start of a section, never trailing. A `##`
with no messages after it is a lint error (GC04).

Final copy comes from a copywriter. The script's placeholder values are the
display name in plain English; SKILL.md Step 3 adds them for every id the
component references and Step 5 lists them for replacement.

## Context menu

The button that opens the menu is shared: `WidgetMenuButton` renders the small
ghost `moz-button` with the `more.svg` icon wired to `menuId`, and takes a class
name, the menu id, the l10n id and an optional `ref`. The trailing block of every widget menu
is shared too: `<WidgetMenuFooter>` renders, in a fixed order, a divider,
Change size, Move, Hide widget, and Learn more (which it opens in a **new
tab**). With nothing of the widget's own above the footer, that leading divider
renders as a stray separator, hence `showDivider={false}`. The example widget
shows the full button, `panel-list` and footer markup.

`SizeSubmenu` owns the resize submenu — it uses the `useSizeSubmenu` hook
internally, so you do not wire `sizeSubmenuRef` yourself, and you must NOT
hand-roll a `useEffect` + `composedPath()` listener (React's synthetic `onClick`
does not cross the `panel-list` shadow-DOM boundary). Horoscopes passes it
the same way as the example.

`WidgetMenuFooter` renders `MoveSubmenu` for you (reads/writes `widgets.order`
via `resolveWidgetOrder`, renders nothing when the widget can't move), dispatches
the Hide pref + `widgets_enabled` telemetry, and opens the Learn more link with
`where: "tab"`. `onLearnMore` is optional and fires only the extra `learn_more`
`widgets_user_event` — do NOT dispatch `OPEN_LINK` yourself.

## Telemetry

`useWidgetTelemetry({ dispatch, widget: ENTRY, widgetSize })` returns:

- `impressionRef`: attach it to the widget's root element; it fires
  `widgets_impression` once through its own `IntersectionObserver`.
- `recordUserAction(action, { source, value })` for interactions
  (`widgets_user_event`): `value` sets `action_value`, and a `size` option
  overrides the reported `widget_size`, as the resize handler does.
- `recordEnabled` (`widgets_enabled`), `recordImpression` (a manual one-shot)
  and `recordError` (`widgets_error`).

The hook keys every event on the entry's `telemetryName`, so do not hand-build
`WIDGETS_IMPRESSION` / `WIDGETS_USER_EVENT` payloads or wire your own
`IntersectionObserver`.

## Standard widget props

Row widgets receive: `dispatch`, `handleUserInteraction`, `isMaximized`,
`widgetsMayBeMaximized`, and `widgetEnabledMap` (a map of `id → boolean` for which
widgets are currently active — used by `MoveSubmenu` and any cross-widget checks).
Every widget uses all of them except `isMaximized`: the widget's own
`handleChangeSize` and `onLearnMore` callbacks call `handleUserInteraction` to
clear the "New" badge (the footer fires them but does not call it itself), and
the footer takes the map and the maximise flag. A widget that takes its size
from a row-wrapper (see sidebar variant) also receives a `size` prop.

## WidgetWrapper is a container concern

`Widgets/WidgetWrapper.jsx` applies `widget-wrapper col-4` and drag-and-drop
plumbing. The container wraps widgets with it, so the widget component renders
its own `<article>` root (SKILL.md Step 2 item 3) and does not import
WidgetWrapper itself.

## Trainhop namespaces

Trainhop config arrives as one `trainhopConfig.<type>` object per `type` in the
Nimbus `newtabTrainhop` payload (`PrefsFeed._getTrainhopConfig`). A widget is
read from two of them:

- **Shared keys** under `trainhopConfig.widgets.*`, named by the entry's
  `trainhopEnabledKey`, `trainhopSizeKey` and `trainhopSidebarKey` (camelCase
  id + suffix: `{key}Enabled`, `{key}Size`, `{key}Sidebar`), plus
  `trainhopConfig.widgetsSettings.*` for the two `widgetsSettings*` keys.
- **A dedicated namespace**, `trainhopConfig.{trainhopNamespace}`, named
  `widget` + PascalCase id (`widgetPictureOfTheDay`, `widgetWeather`). Its
  `visible` reveals the widget in `isWidgetAddable` without writing a pref, its
  `enabled` is written by `PrefsFeed` to the default branch of
  `widgets.{key}.enabled` (a user toggle still wins), and its `size` beats the
  shared size key in `resolveWidgetSize`. A widget can put its own fields
  there too (Privacy, Crossword and Weather do).

Every widget carries a dedicated namespace and that is the shape rollouts are
written in. The registry helpers read it through `isWidgetAddable`, which
`isWidgetEnabled` calls, so a feed that uses `isWidgetEnabled` reads it too
and the entry only declares the name (the requirements
script emits it; SKILL.md Step 2 item 1), and `WidgetsRegistry.test.jsx` has
one `isWidgetAddable` case per namespace (SKILL.md Step 2 item 12). The
`WidgetRegistryEntry` JSDoc says every widget defines one, so it needs no edit.

Leaving the field out fails silently: the widget still works from
`about:config` and from the shared `widgets.{key}Enabled` key, so local testing
passes, but a rollout written against the dedicated namespace does nothing.

Revealing a widget is not the same as showing the widgets section:
`isWidgetsContainerVisible` reads `widgets.system.enabled`,
`trainhopConfig.widgets.enabled`, `trainhopConfig.widgetsSettings.enabled` or
the legacy `widgetsConfig.enabled` Nimbus variable, and never a dedicated
namespace, so an enrolment needs a `widgets` (or `widgetsSettings`) part as
well as the widget's own. SKILL.md Step 5 shows the
multi-payload form that carries both.

## Sidebar variant (optional)

Widgets can render in the sidebar at size `"small"` via `hasSidebar: true` plus a
component in `WIDGET_SIDEBAR_COMPONENTS` (Weather is the only one). This is
not part of the default scaffold. When a spec asks for it, see
[`SidebarVariant.md`](./SidebarVariant.md) for the registry fields and the
row-wrapper / sidebar-component split.

## hide-all is registry-derived

"Hide all widgets" is driven by `getHideAllTargets(prefs, widgetEnabledMap)` and
the `WIDGETS_HIDE_ALL` action — there is no hand-maintained list of `SetPref`
dispatches to edit. Adding a registry entry automatically includes the widget.

**But the hide-all tests still hardcode a count.** The three tests in
`Widgets.test.jsx` (click, Enter, Space) share one helper with a fixed count
and pref list, so because `getHideAllTargets` correctly picks up the new
widget, all three fail until that one helper is edited (SKILL.md Step 2 item
14). Budget for this file in every scaffold. (Deriving the count from
`getHideAllTargets` would stop this recurring.)

## Action types must be alphabetically sorted

The action types in `common/Actions.mjs` are alphabetically sorted, and a test in
`test/jest/common/Actions.test.js` asserts it. Only relevant if your widget needs
new `WIDGETS_*` action types (most don't). Keep them in order, e.g.
`WIDGETS_..._SEEN` before `WIDGETS_..._SET`.

## Don't use batch()

Newtab is on React 19, which batches state updates automatically, so do not
wrap multiple dispatches in `react-redux`'s `batch()`. Older widgets (Clocks,
Weather, etc.) still use it; don't copy that pattern.

## Learn More URL

All widgets share `https://support.mozilla.org/kb/firefox-new-tab-widgets`, and
`WidgetMenuFooter` opens it (see "Context menu"), so do not hardcode the URL in
your widget. Do not create a widget-specific SUMO page.

## Use the `.jsx` extension for content-src files

Files in `content-src/` must use `.jsx`, not `.js`. The ESLint config only treats
`test/**/*.js` as ES modules; a `.js` file in `content-src/` fails with
`Parsing error: 'import' and 'export' may appear only with 'sourceType: module'`.

## Redux state (optional)

Only add a Redux slice if the widget needs cross-tab persistence or complex shared
state. Simple local state (`useState`) is preferable for transient UI. When in
doubt, don't add Redux — it can be added later.

## Feeds are type-checked

`lib/**/*.mjs` is covered by `./mach lint -l typescript browser/extensions/newtab`
(`tsconfig.json` in the newtab root, with an exclude list of files that still
have errors; a new feed is not on it). The store declaration every feed
carries (SKILL.md Step 2, item 3 under the feed file) is what makes
`this.store` type-check.

Keep JSDoc honest: a `@param` naming a parameter the function does not have, a
duplicate `@returns`, or an `async` function documented as returning a
non-Promise are all errors.

## Tests go in Jest

New per-widget tests live in `test/jest/content-src/components/Widgets/{Name}.test.jsx`
(React Testing Library + `expect()`), alongside `Clocks.test.jsx`,
`RecentSearches.test.jsx`, etc. There is also a `WidgetsRegistry.test.jsx` for
registry-level coverage. Every component test is Jest (feeds have xpcshell
tests under `test/xpcshell/`, see SKILL.md Step 2); `test/jest/test-utils.jsx`
exports `WrapWithProvider`, `stubGlobals` and `mockServices`, and widget tests
(Horoscopes is the model) import `WrapWithProvider` from there to render under
a Redux store. Do not write a local provider wrapper in the new test file,
even where another test has one. A fixture that
renders through the container needs `widgets.enabled: true` as well as the
widget's own prefs, since `isWidgetEnabled` reads it.

Several shared tests hardcode the set of widgets and fail until the new one
joins them. SKILL.md Step 2 items 12 to 15 list the edits.

Add a reducer test too if the widget has a Redux slice: the convention is three
cases in `test/jest/common/Reducers.test.jsx` (initial state, the update action
merges and flips `initialized`, an unrelated action returns the *same object
reference*). Mirror the `PrivacyWidget` block, and send a non-empty payload
in the update case so it shows the data was stored, not left at its default.

**Impression tests need their own `IntersectionObserver`.** The global stub in
`test/jest/jest-setup.mjs` has a no-op `observe()` and never invokes its
callback, so any assertion on `WIDGETS_IMPRESSION` fails until the test installs
a capturing mock in `beforeEach` and restores it in `afterEach`. Since every
widget gets an impression from `useWidgetTelemetry`, every widget test hits this.
Copy the block from `PictureOfTheDay.test.jsx` — it also shows the right shape
for asserting the impression fires exactly *once* by invoking the callback twice.

**Test the widget's own handlers, not just that the menu renders.** The shared
pieces are covered elsewhere (`WidgetMenuFooter.test.jsx`, `SizeSubmenu.test.jsx`,
`useWidgetTelemetry.test.jsx`), so what your test has to prove is that *this*
widget wires them correctly. At minimum: assert the menu button carries
`newtab-{css-class}-widget-open-menu-button` as its `data-l10n-id`; render with
`widgetsMayBeMaximized` true (the size submenu is not rendered otherwise), fire
a click on `#{css-class}-size-submenu panel-item[data-size="..."]` for a size
in `validSizes` other than the default, and assert the `change_size` event
carries both `action_value` **and** `widget_size` as the new size (dropping the
`size` option silently reports the pre-change size), plus that
`handleUserInteraction` was called. Skip the resize case for a single-size
widget. `useSizeSubmenu` resolves via `composedPath()`, so `fireEvent.click`
works in jsdom.
