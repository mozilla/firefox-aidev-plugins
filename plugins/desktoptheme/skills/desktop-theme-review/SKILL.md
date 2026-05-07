---
name: desktop-theme-review
description: Conventions for reviewing CSS, SVG, and front-end theme patches in Firefox's desktop chrome and shared toolkit theming layers.
---

## Standing Conventions

### Design tokens & variables
1. Use design tokens (space, size, icon-size, font-size, font-weight, border-radius, color, opacity, focus-outline) instead of literal px/rem/hex values. Tokens carry semantic meaning and adapt to dark mode, HCM, and Nova; raw values do not.
2. Do not use base/primitive tokens (`--color-gray-50`, `--color-violet-70`, etc.) directly in component CSS. Define a semantic local variable that aliases the base token, or use the appropriate semantic token (`--text-color`, `--background-color-box`, `--border-color`). The stylelint `use-design-tokens` rule enforces this.
3. Edit token values in the JSON sources under `toolkit/themes/shared/design-system/src/tokens/` and run `./mach buildtokens`; never hand-edit the generated `dist/tokens-*.css` files.
4. New module-wide custom properties belong in the relevant tokens JSON or a component-scoped `.css` file, not scattered across consumer stylesheets. If a value is used once, inline it instead of inventing a variable.

### Localization & RTL
5. Use logical properties (`margin-inline-*`, `padding-inline-*`, `inset-inline-*`, `border-inline-*`, `border-start-start-radius`, etc.) rather than `left`/`right`. For background/transform-based assets that need mirroring, use `:dir(rtl)` (or `:-moz-locale-dir(rtl)` in XUL) to override or supply a mirrored asset. Test RTL via `intl.l10n.pseudo = bidi`.
6. New user-visible strings live in Fluent (`.ftl`); changing the meaning of a string requires a new Fluent ID. Fluent review is required for `.ftl` changes; reusable components must work with `data-l10n-id` and `data-l10n-attrs`.

### Accessibility & High Contrast Mode
7. Do not rely on `box-shadow` for focus rings or borders that must remain visible — they are stripped in HCM. Use `outline` (with `--focus-outline`/`--focus-outline-offset`) or `border` instead.
8. When overriding colors, override foreground and background as a pair, and prefer the existing `--button-*`, `--text-color*`, `--border-color*` semantic tokens over hand-rolled `prefers-contrast`/`forced-colors` blocks — the tokens already handle those modes. If you must media-query, prefer `@media (forced-colors)` for Windows HCM and `@media (prefers-contrast)` for the broader case; do not duplicate rules across both.
9. Avoid font sizes below 12px in chrome; macOS already shrinks `font: menu` to 11px and going smaller hits accessibility limits. For deemphasized text use `--text-color-deemphasized` (and `var(--font-size-small)` only when truly needed), not hardcoded grays or 11px values.

### Selectors & specificity
10. Prefer the child combinator (`>`) over descendant selectors when the structure is known, and prefer class selectors over element selectors. Use `:where()` to keep specificity low when adding rules that should be easy to override. Avoid `!important` unless overriding another `!important` declaration; document why with a comment when you must.
11. Avoid `:has()` in selectors that match frequently or in tab-strip/urlbar/menu hot paths — it is expensive. Restructure markup to expose an attribute or class instead.
12. Boolean attributes follow HTML semantics (`disabled`, `hidden`, `checked`, `open`): match presence (`[disabled]`), not `[disabled="true"]`. Do not write `="true"` in selectors.

### CSS structure
13. Use nesting to group related rules under a common selector, but cap nesting depth (stylelint enforces this) and unnest rules whose selectors don't actually share the parent's scope. Don't nest just to deduplicate a selector fragment if the result is harder to read.
14. Use `light-dark()` for two-value color pairs instead of duplicating rules under `prefers-color-scheme` media queries. `light-dark()` only works for color values; for non-color light/dark variants, factor into a custom property.
15. Omit unit on `0` (`margin: 0`, not `0px`) — except inside `calc()` where `0px` is required for the calculation to type-check.

### SVG
16. New icons follow the `{name}-{variant}-{size}.svg` convention; omit the size suffix for the default 16px icon, and use `-12` / `-20` / etc. for explicit sizes. Icons must be square at the documented size; non-square assets get bounced back to UX. Place shared icons under `toolkit/themes/shared/icons/` (or `browser/themes/shared/icons/` for browser-only); feature-specific assets stay in the feature folder.
17. SVGs must include the MPL license header, use 2-space indentation with one element per line, and use `fill="context-fill"` (and `context-fill-opacity`, `context-stroke` as needed) so callers can recolor via `-moz-context-properties`. Strip Figma metadata (`data-figma-*`), unused `<defs>`, no-op `clip-path`s, editor namespaces, and useless ids before landing. Run new SVGs through svgomg or equivalent.

### Testing & process
18. Patches touching `.ftl` need `#fluent-reviewers`; patches touching shared CSS/icons need `#desktop-theme-reviewers`; reusable widgets under `toolkit/content/widgets/` need `#reusable-components-reviewers`. Don't request review across the world — the Herald hooks pick the right groups from path globs.
19. Run `./mach lint --fix --outgoing` (Prettier + stylelint) before submitting. If you add a new `.css` file or icon, also confirm `browser_all_files_referenced.js` and `browser_parsable_css.js` still pass — unused custom properties and dangling references fail those tests. New reusable components must be registered in `toolkit/content/customElements.js` to avoid the all-files-referenced failure.

## Active Campaigns (transient)

- **Nova redesign tokens & overrides.** A second token layer (`*.nova.tokens.json`, `browser.nova.enabled` / `browser.theme.native-theme` prefs, `--ai-*` and Smart Window variables) is being layered on top of existing tokens. New CSS should keep Nova-specific overrides scoped (`@media -moz-pref("browser.nova.enabled")` or `:root[lwtheme]` etc.) and avoid hand-rolling values that the Nova token import will eventually supply. *Context: likely to fade once Nova ships and the override layer is collapsed into the base tokens.*
- **Settings Redesign (SRD) — config-based prefs.** Settings panes are being converted from hand-written XUL to config-driven `setting-group` / `setting-pane` / `setting-control` rendered from `Preferences.addSetting(...)` configs. New settings should be added via config, not new XUL; old XUL remains gated on `browser.settings-redesign.enabled` until the migration is complete. *Context: likely to fade once all panes are converted and the legacy XUL paths are removed.*
- **`--in-content-*` removal.** Legacy `--in-content-button-*`, `--in-content-item-*`, `--in-content-border-color`, `--in-content-page-background`, etc. are being replaced with semantic tokens (`--button-*`, `--background-color-*`, `--border-color`, `--color-accent-primary-selected`). Don't introduce new uses of `--in-content-*` variables; replace them when you touch nearby code. *Context: likely to fade once the variable set is fully removed from `toolkit/themes/shared/in-content/common-shared.css`.*

## Common Pitfalls

- Using `--toolbar-bgcolor` (which can be transparent and is meant to layer over the toolbox) as a flat opaque background.
- Using `--arrowpanel-*` colors outside `:-moz-lwtheme` contexts — they are intended for webextension-themed surfaces.
- Hardcoding `font-weight: 600`/`590`/`bold` instead of `var(--font-weight-bold)` (now `--font-weight-semibold`) or `--heading-font-weight`.
- Forgetting that `prefers-contrast` matches on macOS Increased Contrast as well — rules guarded by it must work on macOS, not just Windows HCM. Use `(forced-colors)` when the rule is genuinely Windows-HCM-specific.
- Adding `transition` / `animation` without a `@media (prefers-reduced-motion: no-preference)` guard for movement-based effects.
- Using a fixed `px` `font-size` in chrome — chrome inherits the OS menu font and px values break OS-density and zoom expectations. Use `em`, `1lh`, or font-size tokens.
- Adding `display: none` to elements that should remain in the a11y tree; use `-moz-subtree-hidden-only-visually` or `visibility: hidden` when the tree must be preserved.
- Treating `:active` and `[selected]`/`[open]` as the same state — they are visually distinct and serve different purposes; don't conflate them in HCM rules.
- Setting widths/positions in `px` for elements whose size depends on text (tabs, menu items, urlbar): use `em` or `lh` so they scale with system font size and per-platform font defaults.
- Fighting `moz-button` styling with `::part()` overrides instead of using the documented attributes (`type`, `size`, `iconSrc`, theme tokens). `::part` is fragile across redesigns.

## File-Glob Guidance

### `browser/themes/shared/**` and `toolkit/themes/shared/**`
- Keep platform-specific tweaks in `browser/themes/{linux,osx,windows}/` (or via `@media (-moz-platform: ...)`) — never inline platform hacks in shared files.
- New shared variables must be referenced from at least two consumers, otherwise inline the value.

### `browser/themes/shared/tabbrowser/**`
- The tab strip is performance-sensitive: avoid `:has()`, avoid setting custom properties on every tab, and prefer setting state attributes on `#tabbrowser-tabs` over recomputing per-tab. Mind both `[orient="horizontal"]` and `[orient="vertical"][expanded]` modes plus pinned/unpinned and split-view variants when adding rules. Tab tokens live in `tab.tokens.json`.

### `browser/themes/shared/urlbar*/**`
- Treat the urlbar as its own size domain: it has a platform-specific font scale, its own `--urlbar-*` and `--urlbarview-*` tokens, and its own border-radius scheme (with a separate inner radius for the view). Don't reach for global space tokens without confirming they produce consistent spacing across platforms; prefer urlbar-scoped variables.

### `browser/themes/addons/**` (built-in themes)
- Express theme colors via the `manifest.json` `colors` block whenever possible; only reach into `*.css` for selectors and effects that the manifest cannot express. Don't override design tokens from a theme stylesheet — use the manifest's color keys so non-built-in themes behave consistently.

### `toolkit/themes/shared/design-system/**`
- This directory generates code; only `src/tokens/**.json` and `config/tokens-config.js` are hand-edited. Always rebuild via `./mach buildtokens` and commit the regenerated `dist/` output in the same patch.

### `toolkit/content/widgets/moz-*/**` (reusable components)
- Reusable components must work without a wrapping page context: they need a Storybook story, default-export class, and tokens/CSS variables for any color/spacing/sizing knob a consumer might tweak. Don't hardcode chrome-only or in-content-only assumptions; use semantic tokens that resolve correctly in both. (campaign) When adding properties, also expose them as Storybook controls.

### `*.svg` under any theme directory
- See standing rule 17. Confirm the asset renders correctly in light, dark, and high-contrast modes before landing.

## Review Checklist

- [ ] Are all colors, spaces, sizes, font-sizes, font-weights, and radii expressed via design tokens (or feature-scoped variables aliasing tokens)?
- [ ] Logical properties used everywhere; RTL spot-checked with `intl.l10n.pseudo = bidi`?
- [ ] HCM behavior verified — no reliance on `box-shadow` for visible borders/focus, foreground+background overridden as pairs, `forced-colors` vs `prefers-contrast` used appropriately?
- [ ] New strings have new Fluent IDs; meaning changes get fresh IDs; `#fluent-reviewers` requested for `.ftl` edits?
- [ ] Selector specificity is low — child combinator preferred, no `!important` without justification, no `:has()` in hot paths?
- [ ] SVGs follow naming/size conventions, use `context-fill`, MPL header present, Figma metadata stripped?
- [ ] Boolean attributes treated as presence-only (`[disabled]`, not `[disabled="true"]`)?
- [ ] `transition`/`animation` guarded by `prefers-reduced-motion: no-preference` when movement is involved?
- [ ] `./mach lint --outgoing` clean, `browser_all_files_referenced.js` and `browser_parsable_css.js` still passing?
- [ ] If touching tokens JSON, was `./mach buildtokens` run and the generated CSS committed?
- [ ] If touching reusable components, are Storybook stories, tests, and `customElements.js` registration updated?
- [ ] **(campaign)** If adding/altering a setting, is it expressed via `Preferences.addSetting` + setting-group config, not new XUL?
- [ ] **(campaign)** Nova-specific overrides scoped behind `@media -moz-pref("browser.nova.enabled")` (or equivalent) rather than mutating base tokens?

## House style references

- [CSS Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- [SVG Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/svg_guidelines.html)
- [RTL Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/rtl_guidelines.html)
- [JavaScript Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_js.html)
- [Fluent for Firefox Developers](https://firefox-source-docs.mozilla.org/l10n/fluent/tutorial.html)