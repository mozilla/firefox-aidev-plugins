/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// eslint-disable-next-line no-unused-vars
import React, { useCallback, useRef } from "react";
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
  isMaximized,
  widgetsMayBeMaximized,
}) {
  const prefs = useSelector(state => state.Prefs.values);
  // If the widget has a Redux state slice:
  // const widgetData = useSelector(state => state.ExampleWidget);

  const impressionFired = useRef(false);

  // @nova-cleanup(remove-pref): Remove novaEnabled and this check; always use prefs[PREF_EXAMPLE_WIDGET_SIZE] directly after Nova ships
  const novaEnabled = prefs[PREF_NOVA_ENABLED];
  const isSmallSize = novaEnabled
    ? prefs[PREF_EXAMPLE_WIDGET_SIZE] === "small"
    : isMaximized;
  let widgetSize;
  if (novaEnabled) {
    // Default is "medium". If spec supportsSmallSize = yes, "small" is also valid.
    widgetSize = prefs[PREF_EXAMPLE_WIDGET_SIZE] || "medium";
  } else {
    widgetSize = isSmallSize ? "small" : "medium";
  }

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
          widget_size: widgetsMayBeMaximized ? widgetSize : "medium",
        },
      })
    );
  }, [dispatch, widgetSize, widgetsMayBeMaximized]);

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
            widget_size: widgetsMayBeMaximized ? widgetSize : "medium",
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
            widget_size: widgetsMayBeMaximized ? widgetSize : "medium",
          },
        })
      );
    });
    // Only call handleInteraction() here if the widget is interactive.
    handleInteraction();
  }

  function handleResize(size) {
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
            widget_size: widgetsMayBeMaximized ? size : "medium",
          },
        })
      );
    });
  }

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
            widget_size: widgetsMayBeMaximized ? widgetSize : "medium",
          },
        })
      );
    });
  }

  const maxItems = prefs[PREF_EXAMPLE_WIDGET_MAX_ITEMS];

  return (
    <article
      // @nova-cleanup(remove-conditional): Remove novaEnabled check; always apply col-4 and size class after Nova ships
      className={`example-widget widget ${novaEnabled ? `col-4 ${widgetSize}-widget` : ""} ${isSmallSize ? "is-small" : ""} ${isMaximized ? "is-maximized" : ""}`}
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
            {/* Additional context menu items from spec go here, before Hide */}
            <panel-item
              data-l10n-id="newtab-example-widget-menu-resize-medium"
              onClick={() => handleResize("medium")}
              hidden={widgetSize === "medium"}
            />
            <panel-item
              data-l10n-id="newtab-example-widget-menu-resize-large"
              onClick={() => handleResize("large")}
              hidden={widgetSize === "large"}
            />
            {/* Include the following only if spec supportsSmallSize = yes */}
            <panel-item
              data-l10n-id="newtab-example-widget-menu-resize-small"
              onClick={() => handleResize("small")}
              hidden={widgetSize === "small"}
            />
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
