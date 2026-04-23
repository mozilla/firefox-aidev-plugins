#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Gather widget requirements interactively and print a spec summary for Claude."""

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


def main():
    print("=" * 60)
    print("New Tab Widget Requirements Gatherer")
    print("=" * 60)
    print("Answer each question to generate a widget spec for Claude.")

    # Q1
    display_name = ask(
        "Q1. What is the human-readable display name of the widget?\n    (e.g. 'Reading List', 'Quick Notes')"
    )

    # Q2
    widget_key = ask(
        "Q2. What is the camelCase key for this widget?\n    (e.g. 'readingList', 'quickNotes') — used in pref names and telemetry"
    )

    # Q3 — inferred
    css_class = to_kebab(widget_key)
    print(
        f"\n[Q3 inferred] CSS class: '{css_class}'  (derived from camelCase key — override below if needed)"
    )
    override = input(
        f"> Press Enter to accept '{css_class}', or type a different value: "
    ).strip()
    if override:
        css_class = override

    component_name = widget_key[0].upper() + widget_key[1:]
    telemetry_name = to_snake(widget_key)
    widget_key_upper = to_upper_snake(widget_key)

    # Q4
    extra_menu_items = ask(
        "Q4. Any extra context menu items beyond 'Hide' and 'Learn More'?\n"
        "    List them (e.g. 'Change Location, Toggle Unit') or type 'none'.",
        allow_empty=True,
    )

    # Q5
    interactive_raw = ask(
        "Q5. Will users interact with the widget body itself (clicking buttons, typing, etc.)?\n"
        "    Or is it view-only? Answer 'yes' (interactive) or 'no' (view-only)."
    )
    is_interactive = interactive_raw.lower().startswith("y")

    # Q6 — conditional
    user_actions = ""
    if is_interactive:
        user_actions = ask(
            "Q6. What are the user action type strings for body interactions?\n"
            "    (e.g. 'add_item, toggle_item, delete_item')"
        )

    # Q7
    extra_prefs = ask(
        "Q7. Any widget-specific prefs beyond 'enabled' / 'system.enabled'?\n"
        "    List each with type and default (e.g. 'widgets.readingList.maxItems, int, 20') or 'none'.",
        allow_empty=True,
    )

    # Q8
    redux_state_raw = ask(
        "Q8. Does this widget need its own Redux state slice?\n"
        "    'yes' + brief shape description, or 'no'."
    )
    has_redux = redux_state_raw.lower().startswith("y")
    redux_shape = redux_state_raw[3:].strip() if has_redux else ""

    # Q9
    special_conditions = ask(
        "Q9. Any special enable conditions beyond 'enabled' + 'system.enabled'?\n"
        "    Describe them, or type 'none'.",
        allow_empty=True,
    )

    # Q10
    supports_small_size_raw = ask(
        "Q10. Does this widget support a small size in addition to medium and large?\n"
        "     Answer 'yes' or 'no'."
    )
    supports_small_size = supports_small_size_raw.lower().startswith("y")

    # --- Print summary ---
    print("\n" + "=" * 60)
    print("WIDGET SPEC — hand this to Claude to enter plan mode")
    print("=" * 60)
    print(f"  displayName:    {display_name}")
    print(f"  componentName:  {component_name}")
    print(f"  widgetKey:      {widget_key}")
    print(f"  cssClass:       {css_class}")
    print(f"  telemetryName:  {telemetry_name}")
    print(f"  WIDGET_KEY:     {widget_key_upper}")
    print(f"  interactive:    {'yes' if is_interactive else 'no (view-only)'}")
    if is_interactive and user_actions:
        print(f"  userActions:    {user_actions}")
    print(f"  extraMenuItems: {extra_menu_items or 'none'}")
    print(f"  extraPrefs:     {extra_prefs or 'none'}")
    print(f"  reduxState:     {'yes — ' + redux_shape if has_redux else 'no'}")
    print(f"  specialConditions: {special_conditions or 'none'}")
    print(f"  supportsSmallSize: {'yes' if supports_small_size else 'no'}")
    print("=" * 60)
    print("\nNow enter plan mode: /newtab-widget-scaffold with the spec above.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(1)
