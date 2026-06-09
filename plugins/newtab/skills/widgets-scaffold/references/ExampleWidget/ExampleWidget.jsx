/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// eslint-disable-next-line no-unused-vars
import React, { useCallback, useRef } from "react";
import { useSelector, batch } from "react-redux";
import { actionCreators as ac, actionTypes as at } from "common/Actions.mjs";
import { useIntersectionObserver, useSizeSubmenu } from "../../../lib/utils";
import { WIDGET_REGISTRY, resolveWidgetSize } from "common/WidgetsRegistry.mjs";
import { MoveSubmenu } from "../MoveSubmenu";

// Only present for interactive widgets. Remove entirely for view-only widgets.
const USER_ACTION_TYPES = {
  CHANGE_SIZE: "change_size",
  DO_THING: "do_thing",
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
  const impressionFired = useRef(false);

  const handleIntersection = useCallback(() => {
    if (impressionFired.current) {
      return;
    }
    impressionFired.current = true;
    dispatch(
      ac.AlsoToMain({
        type: at.WIDGETS_IMPRESSION,
        data: {
          // telemetryName from the registry entry (snake_case, no "widget").
          widget_name: "example",
          widget_size: widgetSize,
        },
      })
    );
  }, [dispatch, widgetSize]);

  const widgetRef = useIntersectionObserver(handleIntersection);

  // Call handleUserInteraction("<id>") after any interaction that should mark
  // the widget as "interacted with" for the feature-highlight flow.
  const handleInteraction = useCallback(
    () => handleUserInteraction("example"),
    [handleUserInteraction]
  );

  function handleDoThing() {
    batch(() => {
      // Your main action dispatch goes here, e.g. ac.AlsoToMain(...)

      dispatch(
        ac.OnlyToMain({
          type: at.WIDGETS_USER_EVENT,
          data: {
            widget_name: "example",
            widget_source: "widget",
            user_action: USER_ACTION_TYPES.DO_THING,
            widget_size: widgetSize,
          },
        })
      );
    });
    handleInteraction();
  }

  function handleExampleHide() {
    batch(() => {
      dispatch(
        ac.OnlyToMain({
          type: at.SET_PREF,
          data: { name: EXAMPLE_ENTRY.enabledPref, value: false },
        })
      );
      dispatch(
        ac.OnlyToMain({
          type: at.WIDGETS_ENABLED,
          data: {
            widget_name: "example",
            widget_source: "context_menu",
            enabled: false,
            widget_size: widgetSize,
          },
        })
      );
    });
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
        dispatch(
          ac.OnlyToMain({
            type: at.WIDGETS_USER_EVENT,
            data: {
              widget_name: "example",
              widget_source: "context_menu",
              user_action: USER_ACTION_TYPES.CHANGE_SIZE,
              action_value: size,
              widget_size: size,
            },
          })
        );
      });
    },
    [dispatch]
  );

  // Shared hook: returns a ref to attach to the resize submenu's <panel-list>.
  // It listens at the panel-list root and walks composedPath() to find the
  // clicked size by its data-size attribute. Do NOT hand-roll this — React's
  // synthetic onClick does not cross the panel-list shadow-DOM boundary.
  const sizeSubmenuRef = useSizeSubmenu(handleChangeSize);

  function handleLearnMore() {
    batch(() => {
      dispatch(
        ac.OnlyToMain({
          type: at.OPEN_LINK,
          data: { url: "https://support.mozilla.org/kb/firefox-new-tab-widgets" },
        })
      );
      dispatch(
        ac.OnlyToMain({
          type: at.WIDGETS_USER_EVENT,
          data: {
            widget_name: "example",
            widget_source: "context_menu",
            user_action: "learn_more",
            widget_size: widgetSize,
          },
        })
      );
    });
  }

  // No per-widget Nova gate. The widgets container (Widgets.jsx) already renders
  // WIDGET_ROW_COMPONENTS only in its Nova branch, so this widget mounts only when
  // Nova is enabled — adding a `nova.enabled` early return here would be redundant.

  const maxItems = prefs[PREF_EXAMPLE_MAX_ITEMS];

  return (
    <article
      className={`example widget col-4 ${widgetSize}-widget`}
      ref={el => {
        widgetRef.current = [el];
      }}
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
            {/* Additional context menu items from the spec go here, first. */}

            {/* Resize submenu — only when sizing is available in this layout.
                Include "small" in the map only when validSizes contains it. */}
            {widgetsMayBeMaximized && (
              <panel-item submenu="example-size-submenu">
                <span data-l10n-id="newtab-widget-menu-change-size"></span>
                <panel-list
                  ref={sizeSubmenuRef}
                  slot="submenu"
                  id="example-size-submenu"
                >
                  {["medium", "large"].map(size => (
                    <panel-item
                      key={size}
                      type="checkbox"
                      checked={widgetSize === size || undefined}
                      data-size={size}
                      data-l10n-id={`newtab-widget-size-${size}`}
                    />
                  ))}
                </panel-list>
              </panel-item>
            )}

            {/* Reorder submenu — shared component, reads widgets.order. */}
            <MoveSubmenu widgetId="example" widgetEnabledMap={widgetEnabledMap} />

            <panel-item
              data-l10n-id="newtab-widget-menu-hide"
              onClick={handleExampleHide}
            />
            <panel-item
              data-l10n-id="newtab-example-menu-learn-more"
              onClick={handleLearnMore}
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
