---
name: accessibility-frontend-review
description: Review guidance for Firefox accessibility-frontend patches, covering High Contrast Mode, screen reader exposure, keyboard navigation, design tokens, and Fluent localization.
---

# Accessibility Frontend Review Skill

## Standing Conventions

### High Contrast Mode (HCM) and `forced-colors`
- Whenever a patch sets a background, border, or foreground color, the same selector must produce a sensible result under `@media (forced-colors)`. Use CSS system colors (`ButtonText`, `ButtonFace`, `SelectedItem`, `SelectedItemText`, `Canvas`, `CanvasText`, `GrayText`) — never hex/RGB values that survive into HCM.
- Pair colors correctly: `ButtonText`/`ButtonFace` for default controls, `SelectedItem`/`SelectedItemText` for hover and active interactive states, `Canvas`/`CanvasText` for static surfaces and text. Never mix a custom foreground with a system background.
- When changing the background of an interactive element for hover/active/selected, also update its foreground and add a 1px solid border in the matching system color. Background-only changes are invisible in HCM.
- Drop opacity, transparency, gradients, drop shadows, and `background-image` decorations under `forced-colors`; they either disappear or break contrast.
- Prefer overriding design-token values inside a `@media (forced-colors)` block at `:root`, then consume the same token name throughout. Avoid duplicating selector blocks just to swap colors.
- Distinguish `prefers-contrast` (Increase Contrast — keep the regular palette, add borders, optionally tweak readability) from `forced-colors` (HCM — full system-color palette). Don't lump them together.

### Design Tokens
- Use design-system tokens from `tokens-shared.css` / `tokens-brand.css` — never hardcoded colors, opacities, or font sizes — and pick tokens that match the semantic role (text tokens for text, button tokens for buttons, ghost-button tokens for ghost buttons, link tokens for links).
- Keep token families consistent within a state: if the border uses `--button-border-color-primary-hover`, the background and text must use the matching `-primary-hover` tokens.
- `--font-size-xsmall` is reserved for legal/sponsored microcopy. Do not introduce new uses; flag any new use in a review.
- Use `--text-color` for primary text and `--text-color-deemphasized` only where the design calls for it; verify both resolve correctly in HCM.

### Screen Reader & Semantics
- Every interactive element needs an accessible name. For icon-only buttons, set a non-empty label (Fluent `.aria-label`, `title`, or visible text). Verify with NVDA, VoiceOver, and the Accessibility panel — not just by reading code.
- Expose state changes (pressed, selected, expanded, muted, playing) through ARIA or native semantics; don't rely on visual-only cues. Toggle buttons that change icon/state must also change their accessible name or use `aria-pressed`.
- Prefer native semantic markup (`<h1>`–`<h6>`, `<section>`, `<fieldset>`/`<legend>`, lists) over `role=` patches. Avoid `role="group"` on `<ul>` — it suppresses list semantics.
- Use `aria-labelledby`/`aria-describedby` (or `aria-description` where supported) to associate group headings, helper text, and badges with the focusable control. Set them on the focusable element or its enclosing group, not on a non-focusable sibling.
- Don't rely on transient announcements for content the user must be able to re-read; prefer durable DOM associations. For one-shot announcements (e.g. urlbar tips), use the existing `A11yUtils.announce` framework rather than ad-hoc live regions.
- For ARIA widgets that diverge from the spec (mixed list/grid, multi-cell rows, custom keyboard shortcuts), document the keyboard model and confirm screen-reader behavior across NVDA, VoiceOver, and Orca.

### Keyboard Navigation & Focus
- Every interactive control must be reachable by Tab/arrow keys per its widget pattern. Toolbar buttons should integrate with `ToolbarKeyboardNavigator` (place after the appropriate `<toolbartabstop>`); avoid bare `tabindex` workarounds without justification.
- `Space` and `Enter` should both activate buttons/menubuttons consistently across platforms; `Shift+F10` and the context-menu key should open context menus where applicable.
- After a destructive or transformative action (clear, dismiss, submit), focus must land somewhere predictable — typically the originating control or the next logical target — never lost to `<body>`.
- Modal-style dialogs that block dismissal via `Esc` or backdrop click must move focus into the dialog, set `aria-modal="true"`, and visually convey modality.
- Don't intercept clicks inside shadow DOM and re-dispatch on the host without considering accessibility checks; this breaks `mustHaveAccessibleRule` and assistive-tech targeting.

### Localization (Fluent)
- New user-visible strings go in `.ftl` files with lowercase-hyphenated message IDs. When meaning changes materially, mint a new ID rather than editing in place.
- Pass `data-l10n-args` for variables; never concatenate translated fragments in JS. Use `document.l10n.setAttributes` for runtime-set strings.
- Treat the localized output as opaque: don't substring, slice, or compare against literal translated text in tests. Assert on `data-l10n-id`/`data-l10n-args` instead.
- Patches touching `.ftl` files require review from `#fluent-reviewers`; the Herald hook adds them automatically — don't remove them.

### Testing & A11y Checks
- New focusable widgets must pass mochitest `AccessibilityUtils` checks. When `synthesizeMouseAtCenter` triggers `mustHaveAccessibleRule` failures because of shadow-DOM event re-dispatch, prefer fixing the component's event handling; only use `setEnv` to suppress the rule with a comment explaining why.
- Run patches against pseudolocales (`intl.l10n.pseudo=bidi` and `=accented`) to catch hardcoded strings, truncation, and RTL issues before requesting review.
- For HCM coverage, test on at least one Windows 11 dark theme (e.g. Night Sky) and one light theme (e.g. Desert), plus macOS Increase Contrast where relevant. Screenshots in the review request speed up sign-off considerably.

## Common Pitfalls

- Setting `background-color` for a hover/active/selected state without also updating `color` and `border-color` — invisible in HCM.
- Using `opacity` to dim disabled or de-emphasized UI; HCM users get either invisible text or unreadable contrast. Use `GrayText` or explicit color tokens.
- Hardcoding hex/RGB colors inside a `forced-colors` block instead of using design tokens or system colors.
- Forgetting `alt` on `<img>` (use `alt=""` for purely decorative images, otherwise a real description).
- Adding a `title` whose value is an l10n ID string (e.g. `title="my-button-id"`), exposing the raw identifier to users.
- Removing `Mozilla-style label` association by replacing semantic elements (e.g. `<h4>`) with generic XUL containers and losing heading structure.
- Toggle controls whose label/icon updates visually but whose accessible name stays static (e.g. "Add to taskbar" remaining after the action succeeds).
- Box-shadow focus rings; they vanish in Windows HCM. Use `outline` or `border` with `CanvasText`/`SelectedItem`.
- Live regions or announcements that fire on initial render, spamming screen readers with content the user can already discover statically.
- Long, instructional `aria-label`s on group containers ("Press Tab to move… Press Down to continue"). Users hear them on every entry; keep group labels short and document keyboard shortcuts in SuMo.
- Putting localizable text inside JS string concatenation or computing it from multiple FTL messages.

## File-Glob Guidance

- `browser/themes/shared/**/*.css`, `toolkit/themes/shared/**/*.css`: Verify every color rule has an HCM story. Prefer overriding tokens at `:root` inside `@media (forced-colors)` over duplicating selectors. Watch for `box-shadow` used as focus indication.
- `browser/components/**/*.css`, `browser/extensions/newtab/**/*.scss`: Same HCM rules apply; also check that `--font-size-xsmall` is not introduced for new copy and that hover/active/selected states all swap to `SelectedItem`/`SelectedItemText` pairs.
- `toolkit/content/widgets/moz-*/*.mjs`: Reusable components must expose `aria-label`, `aria-description`, and selected/checked state correctly. Verify Storybook stories match shipped behavior. Don't stop-and-redispatch click events on the host without preserving accessibility-tree targeting.
- `**/*.ftl`, `browser/locales/en-US/**`: Mint new IDs on meaning change; require `#fluent-reviewers`. Keep IDs lowercase-hyphenated. Prefer attribute-style messages (`.label`, `.tooltiptext`) over multiple flat IDs.
- `accessible/**`: Changes to role mapping, name computation, or relation handling can break every consumer; require explicit cross-platform screen-reader verification (NVDA, VoiceOver, Orca).
- `browser/components/preferences/**`: Changes to settings UI must preserve live-region behavior for warnings/alerts that appear on toggle. Telemetry probe shape changes need a migration note.
- `**/test/**/*.js`: Tests should assert `data-l10n-id`/`data-l10n-args` and ARIA attributes, not localized strings. When suppressing an a11y check, leave a comment linking to the underlying issue.

## Review Checklist

1. Every interactive control has a non-empty accessible name; verify with the Accessibility panel or a screen reader, not by reading source.
2. Every color rule resolves correctly under `@media (forced-colors)` — system colors only, paired correctly, with a visible border on interactive surfaces.
3. Hover, active, focus, selected, and disabled states are all visually distinct in default, Increase Contrast, and HCM.
4. No hardcoded colors, font sizes, or opacities; design tokens are used and chosen by semantic role.
5. Focus is reachable via the documented keyboard pattern (Tab, arrows, Space/Enter, Esc) and lands somewhere predictable after every action.
6. State changes (toggled, expanded, selected, muted) are exposed to ARIA, and labels update when meaning changes.
7. Modal dialogs that block soft-dismiss have `aria-modal`, focus management, and a visible modal affordance.
8. New `.ftl` strings have stable IDs, use `data-l10n-args` for variables, and the patch carries `#fluent-reviewers`.
9. Tests assert on l10n IDs and ARIA attributes, not on translated strings; a11y-checks are not silenced without a comment.
10. The patch has been spot-checked against a pseudolocale and against at least one HCM theme; screenshots accompany non-trivial visual changes.
11. New live regions or announcements are necessary, non-redundant, and don't fire on every render.
12. Reusable component changes ship with Storybook coverage and have been verified across NVDA, VoiceOver, and (where feasible) Orca.

## House style references

- [CSS Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- [SVG Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/svg_guidelines.html)
- [RTL Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/rtl_guidelines.html)
- [JavaScript Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_js.html)
- [C++ Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_cpp.html)
- [Using C++ in Firefox Code](https://firefox-source-docs.mozilla.org/code-quality/coding-style/using_cxx_in_firefox_code.html)
- [Fluent Localization Tutorial](https://firefox-source-docs.mozilla.org/l10n/fluent/tutorial.html)