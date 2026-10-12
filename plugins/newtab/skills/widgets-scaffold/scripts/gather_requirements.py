#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Gather widget requirements interactively and print a spec + WIDGET_REGISTRY
entry for Claude."""

import re
import sys


def ask(prompt, allow_empty=False):
    while True:
        answer = input(f"\n{prompt}\n> ").strip()
        if answer or allow_empty:
            return answer
        print("Please provide an answer.")


def to_kebab(camel):
    """Convert camelCase to kebab-case."""
    s = re.sub(r"([A-Z])", r"-\1", camel)
    return s.lower().lstrip("-")


def to_snake(camel):
    """Convert camelCase to snake_case."""
    s = re.sub(r"([A-Z])", r"_\1", camel)
    return s.lower().lstrip("_")


def to_upper_snake(camel):
    return to_snake(camel).upper()


def strip_widget(value):
    """Remove a redundant 'widget' token from a name. The pref namespace is
    already `widgets.`, so a *Widget suffix duplicates it. Returns the cleaned
    value."""
    # camelCase / PascalCase suffix: fooWidget -> foo
    cleaned = re.sub(r"widget", "", value, flags=re.IGNORECASE)
    # snake/kebab leftovers: foo_widget / foo- -> foo
    cleaned = re.sub(r"[_-]+$", "", cleaned)
    cleaned = re.sub(r"^[_-]+", "", cleaned)
    return cleaned


def ask_clean_name(prompt, label):
    """Ask for a name and refuse a 'widget' token (with a suggested fix)."""
    while True:
        value = ask(prompt)
        if "widget" not in value.lower():
            return value
        suggestion = strip_widget(value)
        print(
            f"\n  '{value}' contains 'widget'. The {label} must NOT include it — "
            f"it lives under the `widgets.` namespace, so the suffix is redundant\n"
            f"  (the id and the telemetry name must match without it)."
        )
        choice = input(
            f"> Use '{suggestion}' instead? [Enter = yes, or type another value]: "
        ).strip()
        if not choice:
            if suggestion:
                return suggestion
            print("  Cannot derive a clean name — please type one.")
            continue
        if "widget" in choice.lower():
            print("  That still contains 'widget'. Try again.")
            continue
        return choice


def main():
    print("=" * 60)
    print("New Tab Widget Requirements Gatherer")
    print("=" * 60)
    print("Answer each question to generate a widget spec for Claude.")

    # Q1
    display_name = ask(
        "Q1. What is the human-readable display name of the widget?\n"
        "    (e.g. 'Reading List', 'Quick Notes')"
    )

    # Q2 — enforce no "widget" suffix
    widget_key = ask_clean_name(
        "Q2. What is the camelCase key (registry `id`) for this widget?\n"
        "    (e.g. 'readingList', 'quickNotes') — used in pref names and the order pref.\n"
        "    Do NOT include 'widget' (use 'example', not 'exampleWidget').",
        "widget id",
    )

    # Q3 — css class inferred
    css_class = to_kebab(widget_key)
    print(
        f"\n[Q3 inferred] CSS class: '{css_class}'  (derived from the key — override below if needed)"
    )
    override = input(
        f"> Press Enter to accept '{css_class}', or type a different value: "
    ).strip()
    if override:
        css_class = override

    component_name = widget_key[0].upper() + widget_key[1:]
    widget_key_upper = to_upper_snake(widget_key)

    # Q4 — telemetry name is always the snake_case form of the id
    telemetry_name = to_snake(widget_key)
    print(
        f"\n[Q4 derived] telemetryName: '{telemetry_name}'  (snake_case form of the id)"
    )

    # Q5 — order
    order = ask(
        "Q5. What `order` integer should this widget have?\n"
        "    (The entry is appended to WIDGET_REGISTRY and `order` is the next\n"
        "     free integer after the last entry, retired ones included; array\n"
        "     position is what renders. Type it, or 'next' to let Claude fill it in.)",
        allow_empty=True,
    ) or "next"

    # Q6 — valid sizes
    sizes_raw = ask(
        "Q6. Which sizes does this widget support?\n"
        "    Comma-separated subset of: small, medium, large (e.g. 'medium, large')."
    )
    valid_sizes = [
        s.strip().lower()
        for s in sizes_raw.split(",")
        if s.strip().lower() in ("small", "medium", "large")
    ] or ["medium", "large"]
    # keep canonical order
    valid_sizes = [s for s in ("small", "medium", "large") if s in valid_sizes]

    # Q7 — default size
    default_size = ask(
        f"Q7. What is the default size when the user hasn't chosen one?\n"
        f"    One of {valid_sizes} (default 'medium').",
        allow_empty=True,
    ).lower()
    if default_size not in valid_sizes:
        default_size = "medium" if "medium" in valid_sizes else valid_sizes[0]

    # Q8 — sidebar variant (only meaningful when "small" is supported)
    has_sidebar = False
    if "small" in valid_sizes:
        sidebar_raw = ask(
            "Q8. Should this widget move to the SIDEBAR when its size is 'small'?\n"
            "    Answer 'no' unless the spec requires it: the sidebar holds one widget\n"
            "    and Weather occupies it, so a second needs a layout decision first.\n"
            "    Answer 'yes' or 'no'."
        )
        has_sidebar = sidebar_raw.lower().startswith("y")
    else:
        print("\n[Q8 skipped] No 'small' size, so no sidebar variant.")

    # Q9
    extra_menu_items = ask(
        "Q9. Any extra context menu items beyond 'Hide', 'Learn More', resize, and move?\n"
        "    List them (e.g. 'Change Location, Toggle Unit') or type 'none'.",
        allow_empty=True,
    )

    # Q10
    interactive_raw = ask(
        "Q10. Will users interact with the widget body itself (clicking buttons, typing, etc.)?\n"
        "     Or is it view-only? Answer 'yes' (interactive) or 'no' (view-only)."
    )
    is_interactive = interactive_raw.lower().startswith("y")

    # Q11 — conditional
    user_actions = ""
    if is_interactive:
        user_actions = ask(
            "Q11. What are the user action type strings for body interactions?\n"
            "     (e.g. 'add_item, toggle_item, delete_item')"
        )

    # Q11b — what the body shows
    body_description = ask(
        "Q11b. In a sentence or two, what does the widget body show, and where\n"
        "      does its data come from?"
    )

    # Q12
    extra_prefs = ask(
        "Q12. Any widget-specific prefs beyond enabled / system.enabled / size / interaction?\n"
        "     List each with type and default (e.g. 'widgets.readingList.maxItems, int, 20') or 'none'.",
        allow_empty=True,
    )

    # Q13
    redux_state_raw = ask(
        "Q13. Does this widget need its own Redux state slice?\n"
        "     'yes' + brief shape description, or 'no'."
    )
    has_redux = redux_state_raw.lower().startswith("y")
    redux_shape = redux_state_raw[3:].strip() if has_redux else ""

    # Q14
    special_conditions = ask(
        "Q14. Any special enable conditions beyond enabled + system.enabled\n"
        "     (e.g. needs a backend feed, depends on geolocation)? Describe or 'none'.",
        allow_empty=True,
    )

    trainhop_enabled = f"{widget_key}Enabled"
    trainhop_size = f"{widget_key}Size"
    trainhop_sidebar = f"{widget_key}Sidebar" if has_sidebar else "null"
    sidebar_key_literal = f'"{trainhop_sidebar}"' if has_sidebar else "null"
    # Dedicated Nimbus namespace: `widget` + PascalCase id (widgetPictureOfTheDay).
    trainhop_namespace = f"widget{component_name}"
    # Customize panel label and telemetry source, both derived.
    customize_l10n_id = f"newtab-custom-widget-{css_class}-toggle"
    customize_event_source = f"WIDGET_{telemetry_name.upper()}"

    # --- Print summary ---
    print("\n" + "=" * 60)
    print("WIDGET SPEC — hand this to Claude to enter plan mode")
    print("=" * 60)
    print(f"  displayName:       {display_name}")
    print(f"  componentName:     {component_name}")
    print(f"  widgetKey (id):    {widget_key}")
    print(f"  cssClass:          {css_class}")
    print(f"  telemetryName:     {telemetry_name}")
    print(f"  trainhopNamespace: {trainhop_namespace}")
    print(f"  WIDGET_KEY:        {widget_key_upper}")
    print(f"  order:             {order}")
    print(f"  validSizes:        {valid_sizes}")
    print(f"  defaultSize:       {default_size}")
    print(f"  hasSidebar:        {'yes' if has_sidebar else 'no'}")
    print(f"  interactive:       {'yes' if is_interactive else 'no (view-only)'}")
    if is_interactive and user_actions:
        print(f"  userActions:       {user_actions}")
    print(f"  body:              {body_description}")
    print(f"  extraMenuItems:    {extra_menu_items or 'none'}")
    print(f"  extraPrefs:        {extra_prefs or 'none'}")
    print(f"  reduxState:        {'yes — ' + redux_shape if has_redux else 'no'}")
    print(f"  specialConditions: {special_conditions or 'none'}")

    print("\n" + "-" * 60)
    print("WIDGET_REGISTRY entry (add to common/WidgetsRegistry.mjs):")
    print("-" * 60)
    valid_sizes_js = ", ".join(f'"{s}"' for s in valid_sizes)
    print(
        f"""  {{
    id: "{widget_key}",
    telemetryName: "{telemetry_name}",
    customizeL10nId: "{customize_l10n_id}",
    customizeEventSource: "{customize_event_source}",
    order: {order if order != 'next' else '/* next free integer */'},
    enabledPref: PREF_WIDGETS_{widget_key_upper}_ENABLED,
    sizePref: PREF_{widget_key_upper}_SIZE,
    defaultSize: "{default_size}",
    validSizes: [{valid_sizes_js}],
    hasSidebar: {'true' if has_sidebar else 'false'},
    systemEnabledPref: PREF_WIDGETS_SYSTEM_{widget_key_upper}_ENABLED,
    trainhopEnabledKey: "{trainhop_enabled}",
    trainhopSizeKey: "{trainhop_size}",
    trainhopSidebarKey: {sidebar_key_literal},
    widgetsSettingsVisibleKey: "{widget_key}Visible",
    widgetsSettingsEnabledKey: "{trainhop_enabled}",
    trainhopNamespace: "{trainhop_namespace}",
  }},"""
    )
    print("\n  Pref-key constants to export from the same file:")
    print(
        f'    export const PREF_WIDGETS_{widget_key_upper}_ENABLED = "widgets.{widget_key}.enabled";\n'
        f'    export const PREF_{widget_key_upper}_SIZE = "widgets.{widget_key}.size";\n'
        f'    export const PREF_WIDGETS_SYSTEM_{widget_key_upper}_ENABLED = "widgets.system.{widget_key}.enabled";'
    )
    print(
        f'\n  Also register "widgets.{widget_key}.interaction" (boolean, default false)\n'
        "  in ActivityStream.sys.mjs with the other three; no constant is needed,\n"
        "  Widgets.jsx builds the name from the id. The two enabled prefs start\n"
        '  "off everywhere": getValue: () => !marketGateEnabled() for the user\n'
        "  pref, value: false for the system pref (see SKILL.md Step 2)."
    )
    print(
        "\n  Fluent messages to add to browser/locales/en-US/browser/newtab/newtab.ftl\n"
        "  (values are placeholders; final copy comes from the copywriter):\n"
        f"    newtab-{css_class}-widget-title = {display_name}\n"
        f"    newtab-{css_class}-widget-open-menu-button  (.title and .aria-label = Open {display_name.lower()} menu)\n"
        f"    newtab-{css_class}-menu-learn-more = Learn more\n"
        f"    {customize_l10n_id}  (.label = {display_name})\n"
        "  No home-prefs-* string: about:preferences does not list widgets."
    )
    if has_sidebar:
        print(
            "\n  hasSidebar: true — also register a sidebar component. "
            "See references/SidebarVariant.md."
        )
    print("=" * 60)
    print("\nPaste this summary back to Claude; the skill continues at Step 2.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
