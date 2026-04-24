# Widget Scaffolding Notes

Things that are non-obvious from the ExampleWidget alone. Only update this file
when a gotcha changes — if the example shows it clearly, it doesn't belong here.

## New widgets are Nova-only

All widgets created after the Nova launch do not need classic-enabled fallbacks.
Do not add `PREF_NOVA_ENABLED`, `novaEnabled` conditionals, `.classic-enabled &`
SCSS blocks, or `@nova-cleanup` comments to new widget files. Those patterns exist
only in older widgets pending post-launch cleanup. New widget components also do
not receive `isMaximized` or `widgetsMayBeMaximized` props.

## Build order matters

Generate and register the prefs in `ActivityStream.sys.mjs` **first**, then
run `./mach build faster` before scaffolding the remaining files. The enablement
logic in `Widgets.jsx` reads prefs from the Redux store — if they aren't
registered by the build yet, the widget won't appear even when Nimbus/trainhop
is configured.

## SCSS must be imported in BOTH stylesheets

There are two activity-stream SCSS entry points:

1. `content-src/styles/activity-stream.scss` — classic layout
2. `content-src/styles/nova/activity-stream.scss` — Nova layout

**You must add the `@import` to both files.** If you only add it to one,
the widget will have zero styles in the other layout mode. Nova is the
active layout for most users, so missing the Nova import means the widget
renders completely unstyled.

## `./mach newtab bundle` is required for SCSS changes

`./mach build faster` only copies already-compiled files to the build output.
It does **not** recompile SCSS or JS. After any SCSS or JSX change:

1. Run `./mach newtab bundle` to compile
2. Run `./mach build faster` to copy to the build output
3. Reload `about:newtab`

The compiled artifacts (`css/activity-stream.css`, `css/nova/activity-stream.css`,
`data/content/activity-stream.bundle.js`) are checked into the repo and must be
committed after bundling.

## `widgets.system.enabled` is the parent gate

The entire widgets section (customize panel, about:preferences, and the widget
container on the new tab page) is gated by `widgets.system.enabled`, which
defaults to `false`. Even with all per-widget prefs set correctly, nothing
appears unless this parent gate is enabled via `about:config` or a Nimbus
experiment.

## Base.jsx has TWO CustomizeMenu renders

`Base.jsx` renders `<CustomizeMenu>` in **two separate locations** (for
different layout modes). You must add the `mayHave{Name}Widget` prop to
**both** JSX blocks. If you only add it to one, the customize panel toggle
silently won't appear in the other layout.

Search for `mayHaveListsWidget={` in Base.jsx — you should see two matches.
Add your new prop next to both.

## CustomizeMenu.jsx is a required passthrough

`Base.jsx` passes `mayHave*Widget` props to `<CustomizeMenu>`, which forwards
them to `<ContentSection>`. If you add the prop in `Base.jsx` and `ContentSection.jsx`
but forget `CustomizeMenu.jsx`, the toggle silently never appears.

Files to touch for the Customize panel toggle (all four are required):

1. `Base.jsx` — compute `mayHave{Name}Widget` and `{widgetKey}Enabled`
2. `CustomizeMenu.jsx` — forward the prop
3. `ContentSection.jsx` — add the `switch` case and render the `moz-toggle`
4. `browser/locales/en-US/browser/newtab/newtab.ftl` — add the toggle label string

## AboutPreferences.sys.mjs registration

Widgets must be registered in `AboutPreferences.sys.mjs` to appear in
`about:preferences > Home`. Three changes are needed in this file:

**1. Pref definitions** (in the `preferences` array near the top):
```js
{
  id: "browser.newtabpage.activity-stream.widgets.system.{widgetKey}.enabled",
  type: "bool",
},
{
  id: "browser.newtabpage.activity-stream.widgets.{widgetKey}.enabled",
  type: "bool",
},
```

**2. Settings** (in `_setupHomeGroup`):
```js
Preferences.addSetting({
  id: "{widgetKey}Enabled",
  pref: "browser.newtabpage.activity-stream.widgets.system.{widgetKey}.enabled",
});

Preferences.addSetting({
  id: "{widgetKey}",
  pref: "browser.newtabpage.activity-stream.widgets.{widgetKey}.enabled",
  deps: ["{widgetKey}Enabled"],
  visible: ({ {widgetKey}Enabled }) => {widgetKey}Enabled.value,
});
```

**3. Items array** (add to the `widgets` section's `items`):
```js
{
  id: "{widgetKey}",
  l10nId: "home-prefs-{css-class}-header",
},
```

**4. FTL string** in `browser/locales/en-US/browser/preferences/preferences.ftl`:
```ftl
home-prefs-{css-class}-header =
    .label = {Display Name}
```

## FTL file locations and string formats

Widget strings live in **two separate FTL files**:

- `browser/locales/en-US/browser/newtab/newtab.ftl` — new tab page strings
- `browser/locales/en-US/browser/preferences/preferences.ftl` — about:preferences strings

Add a `##` group comment only at the start of the section, not at the end.
A `##` with no messages after it is a lint error (GC04).

String formats differ by type — do not mix them up:

**Customize panel toggle** — uses `.label` attribute:

```ftl
newtab-custom-widget-{css-class}-toggle =
    .label = {Display Name}
```

**Context menu Learn More** — plain string, no attribute:

```ftl
newtab-{css-class}-widget-menu-learn-more = Learn more
```

**Context menu Hide** — shared string, already exists, do not add it:

```ftl
newtab-widget-menu-hide = Hide
```

## Action types must be alphabetically sorted

The action types array in `common/Actions.mjs` is alphabetically sorted, and
there is an existing test that asserts this ordering. If you add new action
types out of alphabetical order, that test will fail. For example,
`WIDGETS_WORD_OF_THE_DAY_SEEN` must come before `WIDGETS_WORD_OF_THE_DAY_SET`.

## Existing hideAllWidgets tests will break

Adding a new `dispatch(ac.SetPref(...))` call to `hideAllWidgets()` in
`Widgets.jsx` changes the number of `SetPref` dispatches. The existing tests
in `test/unit/content-src/components/Widgets.test.jsx` assert the exact count.
Update the expected count and assertion messages in these tests:

- "should dispatch SetPref actions when hide button is clicked"
- "should dispatch SetPref actions when Enter key is pressed on hide button"
- "should dispatch SetPref actions when Space key is pressed on hide button"

## Use `.jsx` extension for content-src data files

Files in `content-src/` must use the `.jsx` extension, not `.js`. The ESLint
config only treats `test/**/*.js` files as ES modules. A `.js` file in
`content-src/` will fail with: `Parsing error: 'import' and 'export' may
appear only with 'sourceType: module'`.

## handleUserInteraction is conditional

Only include `handleUserInteraction` in the component signature and call it if
the widget has body interactions (Q5 = yes). For view-only widgets, omit it
from both the destructure and the JSX props in `Widgets.jsx`.

## batch() on every multi-dispatch

Any handler that dispatches two or more actions must wrap them in `batch()`
to avoid intermediate renders. This includes `handleHide`, user event handlers,
and any action that pairs a state change with a telemetry dispatch.

## Nimbus trainhop naming convention

The trainhop key follows camelCase + "Enabled" suffix:

- `prefs.trainhopConfig?.widgets?.{widgetKey}Enabled`

Match this exactly — a typo here means the Nimbus experiment path silently
does nothing.

## Full enabled logic blocks (Widgets.jsx and Base.jsx)

These two patterns are not visible from the ExampleWidget component file alone.

**Widgets.jsx** — pref constants and enabled expression to add alongside existing widgets:

```js
const PREF_WIDGETS_{WIDGET_KEY}_ENABLED = "widgets.{widgetKey}.enabled";
const PREF_WIDGETS_SYSTEM_{WIDGET_KEY}_ENABLED = "widgets.system.{widgetKey}.enabled";
```

```js
const nimbus{ComponentName}TrainhopEnabled =
  prefs.trainhopConfig?.widgets?.{widgetKey}Enabled;
const {widgetKey}Enabled =
  (nimbus{ComponentName}TrainhopEnabled ||
    prefs[PREF_WIDGETS_SYSTEM_{WIDGET_KEY}_ENABLED]) &&
  prefs[PREF_WIDGETS_{WIDGET_KEY}_ENABLED];
```

**Base.jsx** — nimbus variables and `mayHave` flag to add alongside existing widgets:

```js
const nimbus{ComponentName}Enabled = prefs.widgetsConfig?.{widgetKey}Enabled;
const nimbus{ComponentName}TrainhopEnabled =
  prefs.trainhopConfig?.widgets?.{widgetKey}Enabled;
const mayHave{ComponentName}Widget =
  prefs["widgets.system.{widgetKey}.enabled"] ||
  nimbus{ComponentName}Enabled ||
  nimbus{ComponentName}TrainhopEnabled;
```

Also add `{widgetKey}Enabled: prefs["widgets.{widgetKey}.enabled"]` to the
`enabledWidgets` object in `Base.jsx`, and pass `mayHave{ComponentName}Widget`
as a prop to **both** `<CustomizeMenu>` renders.

**Widget component itself** — only needed when the component has its own
`return null` guard (i.e. special enable conditions from Q9). Read the trainhop
variable directly from prefs inside the component, mirroring `WeatherForecast.jsx`:

```js
const nimbus{ComponentName}TrainhopEnabled =
  prefs.trainhopConfig?.widgets?.{widgetKey}Enabled;
const {widgetKey}WidgetEnabled =
  nimbus{ComponentName}TrainhopEnabled ||
  prefs["widgets.system.{widgetKey}.enabled"];

if (!{widgetKey}WidgetEnabled || /* other special conditions */) {
  return null;
}
```

For standard widgets without special conditions, skip this — the guard lives
entirely in `Widgets.jsx` and the component always renders when mounted.

## Learn More URL

Always point to: `https://support.mozilla.org/kb/firefox-new-tab-widgets`

Do not create a widget-specific SUMO page — all widgets share this URL.

## null guard in Widgets.jsx

The `if (!(listsEnabled || timerEnabled || ...))` guard controls whether the
entire widget section renders. Add your new `{widgetKey}Enabled` to this OR
expression, otherwise hiding all other widgets will leave your widget orphaned
in an empty container.

## `_Widgets.scss` `:has()` selector

The `.widgets-container` rule uses `:has(.lists), :has(.focus-timer)` to apply
layout when any widget is present. Add your widget's CSS class to this selector
or the container layout won't activate when only your widget is visible.

## Toast string (pending)

`newtab-toast-widgets-hidden` is not yet landed. Once it lands and we rebase,
wire it up to the hide action in the individual widget's hide handler.

## Redux state (optional)

Only add a Redux slice if the widget needs cross-tab persistence or complex
shared state. Simple local state (`useState`) is preferable for transient UI.
When in doubt, don't add Redux — it can always be added later.

## Widget sizes and supportsSmallSize

The size pref always supports `"medium"` and `"large"`. If the spec's
`supportsSmallSize` is `yes`, `"small"` is also valid and must be included
in the context menu and the size derivation logic.

The default size is `"medium"` — use it as the fallback when the pref is not
yet set. See `references/ExampleWidget/ExampleWidget.jsx` for the full size
derivation block and the resize context menu with `hidden` attributes.

## about:preferences registration

Every widget must be registered in `AboutPreferences.sys.mjs` and have a
corresponding FTL string in
`browser/locales/en-US/browser/preferences/preferences.ftl` for its toggle
to appear in `about:preferences`.

## Parent gate pref

The pref `browser.newtabpage.activity-stream.widgets.system.enabled` is a
parent gate for all widgets and defaults to `false`. It must be set to `true`
alongside the widget-specific prefs for the widget to appear. Always include
it in enable instructions.

## Widget resize context menu

Every widget has a resize submenu. Use the `handleChangeSize` / `sizeSubmenuRef`
/ `useEffect` pattern shown in `ExampleWidget.jsx` — do NOT use separate
`<panel-item hidden={...}>` elements. React's synthetic `onClick` does not
traverse the shadow DOM boundary on `panel-list`, so the hidden-item pattern
silently does nothing.

The submenu uses the shared strings `newtab-widget-size-medium`,
`newtab-widget-size-large`, and (if `supportsSmallSize = yes`)
`newtab-widget-size-small` — do not add widget-specific resize FTL strings.

## Nova layout: JSX patterns

Every widget must read `nova.enabled` and apply Nova-specific classes and size
logic. All Nova conditionals are temporary and marked for cleanup when Nova ships.

Add at the top of the component file:

```js
const PREF_NOVA_ENABLED = "nova.enabled";
const PREF_{WIDGET_KEY}_SIZE = "widgets.{widgetKey}.size";
```

Inside the component function, add size derivation:

```js
// @nova-cleanup(remove-pref): Remove novaEnabled and this check; always use prefs[PREF_{WIDGET_KEY}_SIZE] directly after Nova ships
const novaEnabled = prefs[PREF_NOVA_ENABLED];
const isSmallSize = novaEnabled
  ? prefs[PREF_{WIDGET_KEY}_SIZE] === "small"
  : <classic-size-logic>;
let widgetSize;
if (novaEnabled) {
  // Default is "medium". If spec supportsSmallSize = yes, "small" is also valid.
  widgetSize = prefs[PREF_{WIDGET_KEY}_SIZE] || "medium";
} else {
  widgetSize = isSmallSize ? "small" : "medium";
}
```

On the root element's className:

```jsx
// @nova-cleanup(remove-conditional): Remove novaEnabled check; always apply col-4 and size class after Nova ships
className={`{css-class} widget ${novaEnabled ? `col-4 ${widgetSize}-widget` : ""} ${isSmallSize ? "is-small" : ""}`}
```

## Nova layout: SCSS patterns

Classic-specific styles (fixed widths, heights) go inside `.classic-enabled &`
with a `@nova-cleanup(remove-conditional)` comment — see `_ExampleWidget.scss`
for the pattern.

If the widget needs to declare its own `grid-column` span within the Nova
subgrid, use `.nova-enabled &`:

```scss
// @nova-cleanup(remove-conditional): Make default, remove .nova-enabled selector
.nova-enabled & {
  grid-column: span 4;
}
```
