/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// eslint-disable-next-line no-unused-vars
import React, { useCallback, useEffect, useRef } from "react";
import { useSelector, batch } from "react-redux";
import { actionCreators as ac, actionTypes as at } from "common/Actions.mjs";
import { useIntersectionObserver } from "../../../lib/utils";

// Only present for interactive widgets. Remove entirely for view-only widgets.
const USER_ACTION_TYPES = {
  DO_THING: "do_thing",
  DO_OTHER_THING: "do_other_thing",
};

const PREF_NOVA_ENABLED = "nova.enabled";

// Constants for any widget-specific prefs read inside this component.
// Omit if no extra prefs beyond enabled/system.enabled.
const PREF_EXAMPLE_WIDGET_MAX_ITEMS = "widgets.exampleWidget.maxItems";
const PREF_EXAMPLE_WIDGET_SIZE = "widgets.exampleWidget.size";

function ExampleWidget({
  dispatch,
  handleUserInteraction, // omit this param for view-only widgets
}) {
  const prefs = useSelector(state => state.Prefs.values);
  // If the widget has a Redux state slice:
  // const widgetData = useSelector(state => state.ExampleWidget);

  const widgetSize = prefs[PREF_EXAMPLE_WIDGET_SIZE] || "medium";
  const impressionFired = useRef(false);
  const sizeSubmenuRef = useRef(null);

  const handleIntersection = useCallback(() => {
    if (impressionFired.current) {
      return;
    }
    impressionFired.current = true;
    dispatch(
      ac.AlsoToMain({
        type: at.WIDGETS_IMPRESSION,
        data: {
          widget_name: "example_widget",
          widget_size: widgetSize,
        },
      })
    );
  }, [dispatch, widgetSize]);

  const widgetRef = useIntersectionObserver(handleIntersection);

  // Call handleUserInteraction("<widgetKey>") after any interaction that should
  // mark the widget as "interacted with" for the feature highlight flow.
  const handleInteraction = useCallback(
    () => handleUserInteraction("exampleWidget"),
    [handleUserInteraction]
  );

  function handleDoThing() {
    batch(() => {
      // Your main action dispatch goes here, e.g. ac.AlsoToMain(...)

      dispatch(
        ac.OnlyToMain({
          type: at.WIDGETS_USER_EVENT,
          data: {
            widget_name: "example_widget",
            widget_source: "widget",
            user_action: USER_ACTION_TYPES.DO_THING,
            widget_size: widgetSize,
          },
        })
      );
    });
    handleInteraction();
  }

  function handleExampleWidgetHide() {
    batch(() => {
      dispatch(
        ac.OnlyToMain({
          type: at.SET_PREF,
          data: { name: "widgets.exampleWidget.enabled", value: false },
        })
      );
      dispatch(
        ac.OnlyToMain({
          type: at.WIDGETS_ENABLED,
          data: {
            widget_name: "example_widget",
            widget_source: "context_menu",
            enabled: false,
            widget_size: widgetSize,
          },
        })
      );
    });
    // Only call handleInteraction() here if the widget is interactive.
    handleInteraction();
  }

  const handleChangeSize = useCallback(
    size => {
      batch(() => {
        dispatch(
          ac.OnlyToMain({
            type: at.SET_PREF,
            data: { name: PREF_EXAMPLE_WIDGET_SIZE, value: size },
          })
        );
        dispatch(
          ac.OnlyToMain({
            type: at.WIDGETS_USER_EVENT,
            data: {
              widget_name: "example_widget",
              widget_source: "context_menu",
              user_action: "resize",
              action_value: size,
              widget_size: size,
            },
          })
        );
      });
    },
    [dispatch]
  );

  useEffect(() => {
    const el = sizeSubmenuRef.current;
    if (!el) {
      return undefined;
    }
    const listener = e => {
      const item = e.composedPath().find(node => node.dataset?.size);
      if (item) {
        handleChangeSize(item.dataset.size);
      }
    };
    el.addEventListener("click", listener);
    return () => el.removeEventListener("click", listener);
  }, [handleChangeSize]);

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
            widget_name: "example_widget",
            widget_source: "context_menu",
            user_action: "learn_more",
            widget_size: widgetSize,
          },
        })
      );
    });
  }

  // @nova-cleanup(remove-gate): Remove this guard and PREF_NOVA_ENABLED after Nova ships
  if (!prefs[PREF_NOVA_ENABLED]) {
    return null;
  }

  const maxItems = prefs[PREF_EXAMPLE_WIDGET_MAX_ITEMS];

  return (
    <article
      className={`example-widget widget col-4 ${widgetSize}-widget`}
      ref={el => {
        widgetRef.current = [el];
      }}
    >
      <div className="example-widget-title-wrapper">
        <h3 className="newtab-example-widget-title">Example Widget</h3>
        <div className="example-widget-context-menu-wrapper">
          <moz-button
            className="example-widget-context-menu-button"
            iconSrc="chrome://global/skin/icons/more.svg"
            menuId="example-widget-context-menu"
            type="ghost"
          />
          <panel-list id="example-widget-context-menu">
            {/* Additional context menu items from spec go here, before size submenu */}
            <panel-item submenu="example-widget-size-submenu">
              <span data-l10n-id="newtab-widget-menu-change-size"></span>
              <panel-list
                ref={sizeSubmenuRef}
                slot="submenu"
                id="example-widget-size-submenu"
              >
                {/* Include "small" in the map only if spec supportsSmallSize = yes */}
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
            <panel-item
              data-l10n-id="newtab-widget-menu-hide"
              onClick={handleExampleWidgetHide}
            />
            <panel-item
              data-l10n-id="newtab-example-widget-menu-learn-more"
              onClick={handleLearnMore}
            />
          </panel-list>
        </div>
      </div>

      {/* Widget body */}
      <div className="example-widget-body">
        <p>Widget content goes here. Max items: {maxItems}</p>
        <moz-button
          data-l10n-id="newtab-example-widget-do-thing"
          onClick={handleDoThing}
        />
      </div>
    </article>
  );
}

export { ExampleWidget };
