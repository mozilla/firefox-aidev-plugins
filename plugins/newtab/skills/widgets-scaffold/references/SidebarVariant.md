# Sidebar variant (optional)

Most widgets render in the widget row only. A widget can *also* render in the
sidebar when its effective size is `"small"`; Weather is the only widget that
does. You do **not** need this for a standard widget.

The scaffold does not cover adding a second sidebar widget. The sidebar holds
one (`WidgetsSidebar.jsx`: a second one overflows into the content band below)
and Weather occupies that slot; the row keeps Weather out only through its
`widgetEnabledMap` entry (`weatherEnabled && !weatherGoesToSidebar`) and a
Weather case in `hasContentAreaWidgets` in `WidgetsRegistry.mjs`; and nothing
passes `handleUserInteraction` in the sidebar, so the "New" badge cannot clear
from there. If the spec asks for sidebar placement, stop and raise those three
with the user instead of scaffolding around them. The rest of this file
describes how Weather's variant is wired, for use once that decision exists.

Three things differ from the default scaffold: the registry entry gains a few
fields, `WidgetsComponentRegistry.jsx` registers a second component, and the
widget body takes `size` from its props instead of calling `resolveWidgetSize`
itself (`ExampleWidget.jsx` resolves its own size, so add `size` to its
destructured props and drop that call).

## 1. Registry entry (`common/WidgetsRegistry.mjs`)

Add `hasSidebar` and a trainhop sidebar key; make sure `validSizes` includes
`"small"`:

```js
{
  id: "example",
  telemetryName: "example",
  customizeL10nId: "newtab-custom-widget-example-toggle",
  customizeEventSource: "WIDGET_EXAMPLE",
  order: 5,
  enabledPref: PREF_WIDGETS_EXAMPLE_ENABLED,
  sizePref: PREF_EXAMPLE_SIZE,
  defaultSize: "small",
  validSizes: ["small", "medium", "large"],
  hasSidebar: true,                      // <- moves to sidebar at size "small"
  systemEnabledPref: PREF_WIDGETS_SYSTEM_EXAMPLE_ENABLED,
  trainhopEnabledKey: "exampleEnabled",
  trainhopSizeKey: "exampleSize",
  trainhopSidebarKey: "exampleSidebar",  // <- null for non-sidebar widgets
  widgetsSettingsVisibleKey: "exampleVisible",
  widgetsSettingsEnabledKey: "exampleEnabled",
  trainhopNamespace: "widgetExample",
}
```

`hasSidebar` must be set explicitly: size alone is not enough, because a widget
may support `"small"` and still stay in the row. `resolveWidgetHasSidebar(entry,
prefs)` reads `trainhopSidebarKey` first (so trainhop can override placement),
then falls back to the static `hasSidebar` flag.

## 2. Component registry (`Widgets/WidgetsComponentRegistry.jsx`)

Register two thin wrappers around the same widget component — one for the row,
one for the sidebar. The row wrapper resolves the size from the registry and
passes it as a `size` prop, forwarding everything else the row renderer passes
(`dispatch`, `handleUserInteraction`, `isMaximized`, `widgetsMayBeMaximized`,
`widgetEnabledMap`); the sidebar wrapper hard-codes `size="small"`. The sidebar
container passes only `dispatch`, so the widget must not require the other props
when it renders there:

```jsx
import { WIDGET_REGISTRY, resolveWidgetSize } from "common/WidgetsRegistry.mjs";

const exampleEntry = WIDGET_REGISTRY.find(w => w.id === "example");

function ExampleRowWidget(props) {
  const prefs = useSelector(state => state.Prefs.values);
  const size = resolveWidgetSize(exampleEntry, prefs);
  return <ExampleWidget {...props} size={size} />;
}

function ExampleSidebarWidget({ dispatch }) {
  return <ExampleWidget dispatch={dispatch} size="small" />;
}

export const WIDGET_ROW_COMPONENTS = {
  // ...
  example: ExampleRowWidget,
};

export const WIDGET_SIDEBAR_COMPONENTS = {
  // ...
  example: ExampleSidebarWidget,
};
```

When you use the row-wrapper pattern, the widget component should read `size`
from its props instead of calling `resolveWidgetSize` itself (compare Weather,
whose row wrapper passes `size`, with Clocks and the other row widgets, which
resolve their own). Keep the local name `widgetSize` so the rest of the example
still reads: `const widgetSize = size;`.

In the sidebar the component gets `dispatch` and `size` and nothing else, so the
row-only props are `undefined` there and the component has to cope, as Weather
does:

- call `handleUserInteraction?.("{key}")` rather than `handleUserInteraction(...)`,
  or the Learn more and resize handlers throw in the sidebar;
- derive the maximise flag from prefs instead of the prop, the way
  `Weather.jsx` does (`prefs.trainhopConfig?.widgets?.maximized ||
  prefs["widgets.system.maximized"]`), or the Change size submenu never shows
  in the sidebar and the user cannot resize the widget back into the row;
- `widgetEnabledMap` can stay `undefined`: `MoveSubmenu` reads it with optional
  chaining and offers no move when it is missing.

`WidgetsSidebar.jsx` picks the component up from `WIDGET_SIDEBAR_COMPONENTS`
when `resolveWidgetHasSidebar` is `true` at size `"small"`; at any other size
it renders in the row via `WIDGET_ROW_COMPONENTS`. Keeping it out of the row
while it is in the sidebar is the `widgetEnabledMap` exclusion described at the
top.
