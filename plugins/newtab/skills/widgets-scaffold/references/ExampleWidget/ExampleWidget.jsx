/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at https://mozilla.org/MPL/2.0/. */

// eslint-disable-next-line no-unused-vars
import React, { useCallback } from "react";
import { useSelector, batch } from "react-redux";
import { actionCreators as ac, actionTypes as at } from "common/Actions.mjs";
import { WIDGET_REGISTRY, resolveWidgetSize } from "common/WidgetsRegistry.mjs";
import { SizeSubmenu } from "../SizeSubmenu";
import { WidgetMenuButton } from "../WidgetMenuButton";
import { WidgetMenuFooter } from "../WidgetMenuFooter";
import { useWidgetTelemetry } from "../useWidgetTelemetry";

// CHANGE_SIZE and LEARN_MORE are recorded from the callbacks the shared footer
// fires; add the widget's own actions from the spec (DO_THING is a placeholder).
const USER_ACTION_TYPES = {
  CHANGE_SIZE: "change_size",
  DO_THING: "do_thing",
  LEARN_MORE: "learn_more",
};

// Any extra widget-specific pref read here must also be registered in
// lib/ActivityStream.sys.mjs. The enabled/system.enabled/size/interaction prefs
// are owned by the registry and the scaffold — do not redeclare them.

// Look the entry up once by registry id ("example", never "exampleWidget").
const EXAMPLE_ENTRY = WIDGET_REGISTRY.find(w => w.id === "example");

// The row renderer also passes `isMaximized`; leave it out until something
// needs it rather than pulling it in and silencing the unused-var lint.
function ExampleWidget({
  dispatch,
  handleUserInteraction,
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
  // call `recordUserAction(action, { source, value })` for interactions
  // (`value` sets `action_value`; pass `size` to override the reported
  // `widget_size`). `widget` is the registry entry; its `telemetryName`
  // becomes `widget_name`. The hook also returns `recordImpression`,
  // `recordEnabled`, and `recordError`.
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
      handleInteraction();
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
        // `value` is action_value; `size` overrides the reported widget_size.
        // For a resize they're the new size, but they are distinct fields —
        // without `size` the event would report the pre-change widget_size.
        recordUserAction(USER_ACTION_TYPES.CHANGE_SIZE, {
          source: "context_menu",
          value: size,
          size,
        });
        handleInteraction();
      });
    },
    [dispatch, recordUserAction, handleInteraction]
  );

  // Hide and the "Learn more" link (opened in a new tab) are owned by
  // WidgetMenuFooter. This callback, fired through `onLearnMore`, records the
  // extra learn_more event and clears the badge; do not dispatch OPEN_LINK.
  function handleLearnMore() {
    batch(() => {
      recordUserAction(USER_ACTION_TYPES.LEARN_MORE, { source: "context_menu" });
      handleInteraction();
    });
  }

  // The "New" badge shows until the first interaction flips this pref.
  const hasInteracted = prefs["widgets.example.interaction"];

  return (
    <article
      className={`example widget col-4 ${widgetSize}-widget`}
      ref={impressionRef}
      aria-labelledby="example-widget-label"
    >
      <div className="example-title-wrapper">
        <div className="example-badge-title-wrapper">
          {!hasInteracted && (
            <moz-badge
              className="example-new-badge"
              data-l10n-id="newtab-widget-lists-label-new"
            ></moz-badge>
          )}
          {/* `newtab-widget-title` is the shared title typography from
              Widgets/_Widgets.scss; do not restyle the heading. The article's
              aria-labelledby points here, so the title message is also the
              widget's accessible name. */}
          <h2
            id="example-widget-label"
            className="newtab-widget-title"
            data-l10n-id="newtab-example-widget-title"
          />
        </div>
        <div className="example-context-menu-wrapper">
          {/* The shared button fixes the icon, type and size. It is icon-only,
              so its message must exist or a screen reader announces just
              "button": add `newtab-example-widget-open-menu-button` (with
              .title and .aria-label) to newtab.ftl in the same patch. An
              unresolved Fluent id fails silently, unlike a bad import. */}
          <WidgetMenuButton
            className="example-context-menu-button"
            menuId="example-context-menu"
            l10nId="newtab-example-widget-open-menu-button"
          />
          <panel-list className="panel-list-no-icons" id="example-context-menu">
            {/* Widget-specific menu items from the spec go here, ABOVE the
                shared footer. */}

            {/* Shared trailing block for every widget menu, in a fixed order:
                divider, Change size, Move, Hide widget, Learn more (opens in a
                new tab). Pass the Change size submenu via `sizeSubmenu` — or
                pass null for widgets that don't resize. Do NOT hand-roll the
                size submenu / MoveSubmenu / Hide / Learn more items; that is
                what drifts out of sync. */}
            <WidgetMenuFooter
              dispatch={dispatch}
              widgetId={EXAMPLE_ENTRY.id}
              widgetEnabledMap={widgetEnabledMap}
              widgetName={EXAMPLE_ENTRY.telemetryName}
              enabledPref={EXAMPLE_ENTRY.enabledPref}
              widgetSize={widgetSize}
              learnMoreL10nId="newtab-example-menu-learn-more"
              onLearnMore={handleLearnMore}
              // Drop this once the widget has items of its own above the
              // footer; with none, the leading divider is a stray separator.
              showDivider={false}
              sizeSubmenu={
                widgetsMayBeMaximized ? (
                  <SizeSubmenu
                    submenuId="example-size-submenu"
                    sizes={EXAMPLE_ENTRY.validSizes}
                    checkedSize={widgetSize}
                    onChangeSize={handleChangeSize}
                  />
                ) : null
              }
            />
          </panel-list>
        </div>
      </div>

      {/* Widget body: replace with the content from the spec. Every string the
          body shows needs its own message in newtab.ftl; `newtab-example-do-thing`
          below is a placeholder id, not one the scaffold adds. */}
      <div className="example-body">
        <moz-button
          data-l10n-id="newtab-example-do-thing"
          onClick={handleDoThing}
        />
      </div>
    </article>
  );
}

export { ExampleWidget };
