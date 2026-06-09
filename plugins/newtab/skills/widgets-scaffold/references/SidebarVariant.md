# Sidebar variant (optional)

Most widgets render in the widget row only. A widget can *also* render in the
sidebar when its effective size is `"small"` — Weather is the only widget that
does this today. You do **not** need this for a standard widget; reach for it
only when the spec explicitly calls for a sidebar placement.

The widget body (`ExampleWidget.jsx`) is unchanged — it already accepts a `size`.
Only two things differ from the default scaffold: the registry entry gains a few
fields, and `WidgetsComponentRegistry.jsx` registers a second component.

## 1. Registry entry (`common/WidgetsRegistry.mjs`)

Add `hasSidebar` and a trainhop sidebar key; make sure `validSizes` includes
`"small"`:

```js
{
  id: "example",
  telemetryName: "example",
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
}
```

`hasSidebar` must be set explicitly: size alone is not enough, because a widget
may support `"small"` and still stay in the row. `resolveWidgetHasSidebar(entry,
prefs)` reads `trainhopSidebarKey` first (so trainhop can override placement),
then falls back to the static `hasSidebar` flag.

## 2. Component registry (`Widgets/WidgetsComponentRegistry.jsx`)

Register two thin wrappers around the same widget component — one for the row,
one for the sidebar. The row wrapper resolves the size from the registry and
passes it as a `size` prop; the sidebar wrapper hard-codes `size="small"`:

```jsx
import { WIDGET_REGISTRY, resolveWidgetSize } from "common/WidgetsRegistry.mjs";

const exampleEntry = WIDGET_REGISTRY.find(w => w.id === "example");

function ExampleRowWidget({ dispatch, widgetEnabledMap }) {
  const prefs = useSelector(state => state.Prefs.values);
  const size = resolveWidgetSize(exampleEntry, prefs);
  return (
    <ExampleWidget
      dispatch={dispatch}
      size={size}
      widgetEnabledMap={widgetEnabledMap}
    />
  );
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
from its props instead of calling `resolveWidgetSize` itself (compare Weather
and Clocks, which take `size` as a prop, with Sports, which resolves its own).

The container places the component automatically: `resolveWidgetHasSidebar`
returning `true` at size `"small"` routes it to `WIDGET_SIDEBAR_COMPONENTS`;
otherwise it renders in the row via `WIDGET_ROW_COMPONENTS`.
