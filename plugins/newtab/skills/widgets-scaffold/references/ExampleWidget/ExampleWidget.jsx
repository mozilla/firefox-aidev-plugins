/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// eslint-disable-next-line no-unused-vars
import React, { useCallback } from "react";
import { useSelector, batch } from "react-redux";
import { actionCreators as ac, actionTypes as at } from "common/Actions.mjs";
import { WIDGET_REGISTRY, resolveWidgetSize } from "common/WidgetsRegistry.mjs";
import { SizeSubmenu } from "../SizeSubmenu";
import { WidgetMenuFooter } from "../WidgetMenuFooter";
import { useWidgetTelemetry } from "../useWidgetTelemetry";

// Only present for interactive widgets. Remove entirely for view-only widgets.
const USER_ACTION_TYPES = {
  CHANGE_SIZE: "change_size",
  DO_THING: "do_thing",
  LEARN_MORE: "learn_more",
};

// Constants for any extra widget-specific prefs read inside this component.
// The enabled/system.enabled/size prefs are owned by the registry — do not
// redeclare them here. Omit this block if there are no extra prefs.
const PREF_EXAMPLE_MAX_ITEMS = "widgets.example.maxItems";

// Look the entry up once by registry id. NOTE: the id must NOT contain the
// word "widget" — it lives under the `widgets.` pref namespace, so a suffix
// like "exampleWidget" is redundant (and caused a real pref/telemetry bug on
// the Sports widget). Use "example", not "exampleWidget".
const EXAMPLE_ENTRY = WIDGET_REGISTRY.find(w => w.id === "example");

function ExampleWidget({
  dispatch,
  handleUserInteraction, // omit for view-only widgets
  // eslint-disable-next-line no-unused-vars
  isMaximized,
  widgetsMayBeMaximized,
  widgetEnabledMap,
}) {
  const prefs = useSelector(state => state.Prefs.values);
  // If the widget has a Redux state slice:
  // const widgetData = useSelector(state => state.ExampleWidget);

  // Size comes from the registry helper: user-set pref > trainhop suggestion
  // > registry defaultSize. Never read the size pref directly.
  const widgetSize = resolveWidgetSize(EXAMPLE_ENTRY, prefs);

  // Shared telemetry hook. Do NOT hand-build WIDGETS_IMPRESSION /
  // WIDGETS_USER_EVENT payloads or wire up your own IntersectionObserver:
  // attach `impressionRef` to the widget root for the one-shot impression, and
  // call `recordUserAction(action, { source })` for interactions. `widget` is
  // the registry entry; its `telemetryName` becomes `widget_name`. The hook
  // also returns `recordImpression`, `recordEnabled`, and `recordError`.
  const { impressionRef, recordUserAction } = useWidgetTelemetry({
    dispatch,
    widget: EXAMPLE_ENTRY,
    widgetSize,
  });

  // Call handleUserInteraction("<id>") after any interaction that should mark
  // the widget as "interacted with" for the feature-highlight flow.
  const handleInteraction = useCallback(
    () => handleUserInteraction("example"),
    [handleUserInteraction]
  );

  function handleDoThing() {
    batch(() => {
      // Your main action dispatch goes here, e.g. dispatch(ac.AlsoToMain(...))
      recordUserAction(USER_ACTION_TYPES.DO_THING, { source: "widget" });
    });
    handleInteraction();
  }

  const handleChangeSize = useCallback(
    size => {
      batch(() => {
        dispatch(
          ac.OnlyToMain({
            type: at.SET_PREF,
            data: { name: EXAMPLE_ENTRY.sizePref, value: size },
          })
        );
        recordUserAction(USER_ACTION_TYPES.CHANGE_SIZE, {
          source: "context_menu",
          value: size,
          size,
        });
      });
    },
    [dispatch, recordUserAction]
  );

  // Hide and the "Learn more" link (opened in a new tab) are owned by
  // WidgetMenuFooter. This callback only records the extra learn_more event the
  // footer fires through `onLearnMore` — do not dispatch OPEN_LINK yourself.
  function handleLearnMore() {
    recordUserAction(USER_ACTION_TYPES.LEARN_MORE, { source: "context_menu" });
  }

  // No per-widget Nova gate. The widgets container (Widgets.jsx) already renders
  // WIDGET_ROW_COMPONENTS only in its Nova branch, so this widget mounts only when
  // Nova is enabled — adding a `nova.enabled` early return here would be redundant.

  const maxItems = prefs[PREF_EXAMPLE_MAX_ITEMS];

  return (
    <article
      className={`example widget col-4 ${widgetSize}-widget`}
      ref={impressionRef}
    >
      <div className="example-title-wrapper">
        <h3 className="newtab-example-title">Example Widget</h3>
        <div className="example-context-menu-wrapper">
          <moz-button
            className="example-context-menu-button"
            iconSrc="chrome://global/skin/icons/more.svg"
            menuId="example-context-menu"
            type="ghost"
          />
          <panel-list id="example-context-menu">
            {/* Widget-specific menu items from the spec go here, ABOVE the
                shared footer. */}

            {/* Shared trailing block for every widget menu, in a fixed order:
                divider, Change size, Move, Hide widget, Learn more (opens in a
                new tab). Pass the Change size submenu via `sizeSubmenu` — or
                pass null for widgets that don't resize. Do NOT hand-roll the
                size submenu / MoveSubmenu / Hide / Learn more items; that is
                what drifts out of sync (see Bug 2046045 / D306294). */}
            <WidgetMenuFooter
              dispatch={dispatch}
              widgetId="example"
              widgetEnabledMap={widgetEnabledMap}
              widgetName="example"
              enabledPref={EXAMPLE_ENTRY.enabledPref}
              widgetSize={widgetSize}
              learnMoreL10nId="newtab-example-menu-learn-more"
              onLearnMore={handleLearnMore}
              sizeSubmenu={
                widgetsMayBeMaximized ? (
                  <SizeSubmenu
                    submenuId="example-size-submenu"
                    sizes={["medium", "large"]}
                    checkedSize={widgetSize}
                    onChangeSize={handleChangeSize}
                  />
                ) : null
              }
            />
          </panel-list>
        </div>
      </div>

      {/* Widget body */}
      <div className="example-body">
        <p>Widget content goes here. Max items: {maxItems}</p>
        <moz-button
          data-l10n-id="newtab-example-do-thing"
          onClick={handleDoThing}
        />
      </div>
    </article>
  );
}

export { ExampleWidget };
