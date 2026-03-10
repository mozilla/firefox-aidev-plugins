# Widget Scaffolding Notes

Things that are non-obvious from the ExampleWidget alone. Only update this file
when a gotcha changes — if the example shows it clearly, it doesn't belong here.

## Build order matters

Generate and register the prefs in `ActivityStream.sys.mjs` **first**, then
run `./mach build faster` before scaffolding the remaining files. The enablement
logic in `Widgets.jsx` reads prefs from the Redux store — if they aren't
registered by the build yet, the widget won't appear even when Nimbus/trainhop
is configured.

## CustomizeMenu.jsx is a required passthrough

`Base.jsx` passes `mayHave*Widget` props to `<CustomizeMenu>`, which forwards
them to `<ContentSection>`. If you add the prop in `Base.jsx` and `ContentSection.jsx`
but forget `CustomizeMenu.jsx`, the toggle silently never appears.

Files to touch for the Customize panel toggle (all four are required):

1. `Base.jsx` — compute `mayHave{Name}Widget` and `{widgetKey}Enabled`
2. `CustomizeMenu.jsx` — forward the prop
3. `ContentSection.jsx` — add the `switch` case and render the `moz-toggle`
4. `browser/locales/en-US/browser/newtab/newtab.ftl` — add the toggle label string

## FTL file location and string formats

All widget strings go in `browser/locales/en-US/browser/newtab/newtab.ftl`.
Not the `webext-glue/locales/` path (that's a different, generated file).

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
as a prop to `<CustomizeMenu>`.

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
