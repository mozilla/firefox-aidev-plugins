---
description: Durable review guidance for Firefox desktop theme and toolkit theme CSS, covering design tokens, RTL/HCM discipline, theme compatibility, and chrome styling conventions.
---

# Module Scope

- Paths: `browser/themes/**/*`, `toolkit/themes/**/*`
- Bugzilla components: Firefox::Theme, Toolkit::Themes

# Core Reviewers

- Owners: dao, hjones
- Peers: emilio, itiel_yn8, Julian, jules, kcochrane, sfoster, tgiles, mstriemer

# Standing Conventions

## Design tokens

- Prefer existing design tokens over literal values for color, dimension, border-radius, opacity, font-size, and box-shadow. Inline literals (px, hex, rgba) should only appear when no token fits and the value is not aesthetic — application-logic numbers (widths gated on prefs, etc.) stay in feature CSS, not in the design system.
- Token names follow `--<domain>-<element>-<property>[-<modifier>]`, lowercase with dashes; the property comes after the nested element (e.g., `--urlbar-box-background-color`, not `--urlbar-background-color-box`). Domain prefixes (`--urlbar-`, `--tab-`, `--toolbar-`, `--panel-`) are required for tokens scoped to one feature.
- Component tokens live next to the component (`*.tokens.json` / `*.tokens.css`), not in the global `tokens-shared.css`. Only tokens that are genuinely cross-cutting belong in shared output; otherwise they leak into about: pages and unrelated surfaces.
- Don't reach past a semantic token to a base token. Add a new semantic alias rather than referencing palette values directly from feature CSS.

## Localization & RTL

- Use logical properties (`margin-inline-*`, `padding-inline-*`, `inset-inline-*`, `border-{start,end}-{start,end}-radius`, `float: inline-start|end`) instead of left/right. Reach for `:dir(rtl)` / `:-moz-locale-dir(rtl)` only when no logical property exists or when forcing LTR for paths/URLs/code.
- When forcing `direction: ltr` on content like URLs, pair it with `text-align: match-parent` so alignment still follows the surrounding UI.
- Don't reorder size dimensions, units, or numeric tokens for RTL; mirror only icons that imply direction or motion.

## Accessibility & High Contrast

- Don't suppress focus rings or borders with `box-shadow` alone — HCM strips shadows. Use `border` or `outline` for anything that must remain visible under forced colors.
- Disabled-state opacity tokens must resolve to `1` under `prefers-contrast` and `forced-colors`; pair them with explicit `GrayText` / `ButtonFace` color handling rather than relying on opacity alone.
- Deemphasized text/color tokens should likewise resolve to full strength under `prefers-contrast`. When introducing a deemphasis variant, define its contrast-mode value at the token level, not at each call site.

## Theme & cross-platform compatibility

- Prefer styling that works for default, light, dark, and WebExtension (LWT) themes via existing CSS variables and `currentcolor`/inheritance. Avoid hard-coded colors in chrome CSS; if a value must vary by theme, route it through the token layer with the appropriate `:root:not([lwtheme])` / `lwtheme-*` selectors.
- Prefer the `shared/` theme directory over per-platform stylesheets unless the difference is genuinely platform-specific. Don't write rules in `compacttheme.css` that would also affect WebExtension themes.
- Be mindful that toolbox/toolbar background painting now lives on `<body>`; new chrome styles should not assume the toolbox element paints its own background.

## File structure & naming

- New chrome CSS variables that aren't reusable component tokens belong in a domain-specific file (`urlbar.css`, `toolbar.css`, `tabs.css`, `popup.css`) co-located with the feature, not under `toolkit/themes/shared/design-system/src/`. The design-system directory is for genuinely reusable tokens; feature-scoped tokens get reviewed by the feature's peers.
- Don't introduce a CSS variable that's only used once. Inline the value (or, if it represents an aesthetic decision shared with other surfaces, promote it to a token).
- Keep import order: content/global CSS first, then theme CSS, so theme values can override.

## Patch hygiene

- A patch titled "rename" must only rename. Behavior, selector, and value changes belong in separate, explicitly-described commits.
- When tokenizing or refactoring variables, preserve the existing visual result across default/light/dark/LWT/HCM. Do a manual sweep of representative themes before requesting review; don't rely on the diff alone.
- New `*.css` and `*.tokens.json` files need the standard MPL header.

# Active Campaigns (transient)

- **CSS variable → JSON design token migration.** Component variables across `browser/themes` and `toolkit/themes` are being moved into per-component `*.tokens.json` consumed by the design-system build. Naming conventions, file locations, and reviewer routing are still being rationalized; expect churn around what lives under `design-system/src/` vs. next to the component. Context: likely to fade once the token build supports arbitrary feature paths and the bulk of `--toolbar-*`, `--urlbar-*`, `--tab-*`, `--panel-*` variables have been migrated.
- **Nova theme overrides.** A parallel set of token overrides is being imported from Figma and gated on the global Nova pref. CSS that touches affected tokens should not assume a single value — verify rendering with the Nova pref both on and off. Context: likely to fade once the Nova rollout completes and overrides are either promoted to defaults or removed.
- **Sidebar revamp / vertical tabs.** Theme work must be cross-checked against `sidebar.revamp = true` and vertical tab layouts; older sidebar-switcher styling is being phased out and shouldn't gain new dependents. Context: likely to fade once `sidebar.revamp` becomes the only path.

# Common Pitfalls

- Hard-coding small px values (4, 8, 12) where a `--space-*` or `--dimension-*` token already exists, or inventing a new token for a one-off value.
- Using `left`/`right` (margin, padding, border, position) instead of inline-logical equivalents in new code.
- Renaming or removing tokens without aliasing, breaking downstream consumers (extension themes, devtools, about: pages).
- Putting feature-specific tokens (urlbar, tabs, toolbar) into `tokens-shared.css`, leaking them into surfaces that shouldn't see them.
- Mixing a `dist/` token rename with a value change in the same patch — reviewers can't distinguish refactor from regression.
- Setting `box-shadow` for focus indicators or borders that need to survive HCM.
- Using `opacity` to imply disabled state without ensuring it collapses to 1 under `prefers-contrast`/`forced-colors`.
- Adding `!important` without an inline comment justifying it, or to override a rule whose specificity could simply be lowered.
- Forgetting `text-align: match-parent` when forcing `direction: ltr` on a URL/path/code field inside an RTL UI.
- Adding rules to `compacttheme.css` that unintentionally affect LWT/WebExtension themes.

# File-Glob Guidance

- `browser/themes/shared/**/*.css` — Domain-scoped chrome CSS. Keep `--urlbar-*`, `--toolbar-*`, `--tab-*`, `--panel-*` variables here or in their feature's `*.tokens.css`, not in design-system shared output. Watch for tokens leaking across features.
- `toolkit/themes/shared/design-system/src/**` — Reserved for genuinely reusable tokens and components. New feature tokens require justification for living here; the build config is authoritative for what gets emitted to `dist/`.
- `toolkit/themes/shared/design-system/dist/**` — Generated. Don't hand-edit; changes must come from the JSON sources and the build.
- `toolkit/content/widgets/**/moz-*.css` and adjacent `*.tokens.css` — Reusable components. Token overrides (`--g-*` prefixed or otherwise) need a clear use case; don't expose internal layout tokens for external override.
- `browser/themes/{linux,osx,windows}/**` — Platform-specific only. Anything that could live under `shared/` should.
- `*.tokens.json` — Group tokens by category; alias to existing semantic tokens (e.g., `--text-color-deemphasized`) so HCM/`prefers-contrast` handling propagates.
- `browser/components/storybook/**` and design-system docs — Storybook examples must compile against current token names; update them in the same patch as token renames.

# Review Checklist

- [ ] All new color, spacing, font, radius, opacity, and shadow values use existing design tokens, or a new token has been added with proper naming and category.
- [ ] Token names follow `domain-element-property-modifier` ordering and are scoped to the right file (component-local vs. shared).
- [ ] No `left`/`right` in new code where a logical property exists.
- [ ] Focus indicators and disabled states render correctly under `forced-colors` and `prefers-contrast` (no shadow-only outlines, opacity collapses to 1).
- [ ] No new hard-coded colors in chrome CSS — values flow through tokens and respect LWT/dark/light themes.
- [ ] `!important` is absent, or each occurrence has an inline comment.
- [ ] Patch description matches scope: renames don't include behavior changes; refactors note any intentional value drift.
- [ ] Feature-specific tokens are routed to feature reviewers (urlbar, tabbrowser, sidebar, etc.), not just design-system reviewers.
- [ ] Visual sweep covers default + dark + at least one LWT/WebExtension theme; for token-affecting work, also Nova-on and Nova-off.
- [ ] Generated `dist/` files are regenerated from JSON sources, not hand-edited.
- [ ] No new uses of single-use CSS variables; one-off values are inlined or promoted to a real token.
- [ ] License header present on new files; standard 2-space indent and expanded property syntax.

# House style references

- [CSS Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- [SVG Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/svg_guidelines.html)
- [RTL Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/rtl_guidelines.html)
- [JavaScript Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_js.html)