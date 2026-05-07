---
name: home-newtab-review
description: Review guidance for Firefox's Home/New Tab module covering its React/JSX front-end, system modules, telemetry, train-hop compatibility, and design-token usage.
---

# Home/New Tab Review Skill

## Standing Conventions

### Train-hop compatibility (load-bearing)
1. **Assume the New Tab XPI rides separately from the host application.** Any code under `browser/extensions/newtab/` may execute on host versions older than the one it was authored against. Code under `browser/components/newtab/`, `browser/modules/AboutNewTab*`, actors, IDL, IPDL, `firefox.js`, and `FeatureManifest.yaml` does *not* train-hop and ships with the host.
2. **Feature-detect, then shim, then mark.** When calling a host API that may not exist on older supported versions, guard with `typeof X.method === "function"` (or equivalent) and provide a fallback. Annotate the shim with `@backward-compat { version N }` JSDoc so it can be removed once N reaches release. Three releases is the typical compatibility window.
3. **Default values for new prefs/Nimbus variables must be set in `ActivityStream.sys.mjs` `PREFS_CONFIG`,** not (only) in `firefox.js`. Prefs added to `firefox.js` alone are invisible on older hosts. Dynamic prefs (locale/region-derived) belong in `ActivityStream.sys.mjs`'s dynamic computation, never `firefox.js`.
4. **New Nimbus features are not train-hoppable.** Use the `newtabTrainhop` co-enrollment feature with a `trainhopConfig.<feature>.<variable>` payload pattern, not new top-level entries in `FeatureManifest.yaml`. Read with `Prefs.values.trainhopConfig?.<feature>?.<var>` plus a system pref fallback.
5. **String migrations and metric registrations land at least one cycle before the consuming train-hop.** New Fluent IDs added in version N can only be referenced by an XPI targeting N or later; runtime metrics JSON for version N must exist before XPIs reference those metrics.

### Localization
1. **Never hardcode user-facing English in JSX or markup.** Use Fluent via `data-l10n-id` (and `data-l10n-args` where needed). For attribute-only strings, use `.label`/`.aria-label`/`.title` Fluent attributes.
2. **Add a Fluent comment whenever the string's intent isn't obvious from the ID,** especially for short imperatives ("Report", "Hide") that are ambiguous between verbs and nouns to translators.
3. **Prefer brand-new Fluent IDs over `-v2` suffixes** when the meaning of an existing string changes. Provide a Fluent migration recipe under `python/l10n/fluent_migrations/` and verify it with `./mach fluent-migration-test`.
4. **Mind locale fallbacks during train-hops.** New locale strings are not present on older hosts; either gate the consuming code, ship the string ahead of time, or include the string in the XPI's bundled locales.

### Accessibility & High Contrast Mode
1. **Every interactive non-button element with a click handler needs a keyboard story.** Restrict key handlers to `Enter` and `Space`; never trigger on arbitrary keys.
2. **Use the right semantic element first.** Dialogs use `<dialog>`; menus use `panel-list`; toggles use `moz-toggle`; section headings follow document outline (don't skip levels). Reach for `role=` only when the semantic element doesn't fit.
3. **`aria-expanded`, `aria-haspopup`, `aria-label`, `aria-labelledby` are not optional** on context-menu buttons, dialog triggers, or icon-only controls. Position-in-set information (`aria-posinset`/`aria-setsize`) belongs on grouped lists with non-list parents.
4. **HCM (`forced-colors`) must be considered for any new component.** Use `ButtonText`, `SelectedItem`, `Canvas`, `CanvasText` system colors; never rely on `box-shadow` for borders/focus rings; reset gradients to `Canvas` rather than reimplementing them.
5. **`disabled` buttons need the `disabled` attribute,** not just CSS. CSS-only "disabled" still receives focus and click events.

### Design tokens & theming
1. **Use Acorn design tokens (`--space-*`, `--font-size-*`, `--border-radius-*`, `--color-*`, `--border-color-selected`, etc.) over literal values.** When a token doesn't fit, push back on the design rather than introducing a magic number; only reach for raw px for image dimensions or pixel-level positioning of decorative elements.
2. **Avoid `calc()` to combine two tokens.** If you need `calc(var(--space-large) + var(--space-xsmall))`, the design is asking for a value the system doesn't define — use the closest single token or raise the gap with design.
3. **Use logical properties exclusively** (`margin-inline-*`, `padding-block-*`, `inset-inline-*`, `border-start-start-radius`). Reach for physical `left`/`right` only inside an explicitly LTR-forced subtree (e.g., URL/code display) and document why.
4. **`@nova-cleanup` comment any code that exists only to bridge classic and Nova layouts** so it can be found and removed when Nova ships everywhere. Prefer `.nova-enabled & { ... }` nesting over forking entire SCSS files; only fork when the components diverge substantially.
5. **Wallpapers and themes mean text colors aren't fixed.** Use `--newtab-contextual-text-primary-color` and the contextual contrast mixins for anything overlaying user-controlled backgrounds.

### Telemetry & data
1. **Don't introduce new top-level Glean categories without need.** Reuse existing newtab probes; share descriptions via YAML anchors (`&name`/`*name`) when the same field appears in multiple metrics.
2. **Set `data_sensitivity` correctly:** `technical` for app/runtime state, `interaction` for user-driven events. `_enabled` flags are almost always `technical`.
3. **`newtab-content` ping submissions are randomized** through `NewTabContentPing`'s session policy; never call `submit()` directly from feature code. Respect `MAX_UINT32` normalization for any sampling helper that produces 0.0–1.0 values.
4. **Update runtime-metrics JSON files for any metric/ping schema change** intended to ride a train-hop, and add `no_lint: [COMMON_PREFIX]` to runtime-registered metrics that share a prefix.
5. **Tests of telemetry-emitting code assert the dispatched action / metric arguments, not formatted output.** Use `getAttributes` and verify `data-l10n-id` rather than the rendered string; assert metric `.testGetValue()` rather than scraping the DOM.

### State, prefs, and feed wiring
1. **Read prefs through Redux state (`this.props.Prefs.values.<name>` or `this.store.getState().Prefs.values.<name>`)**, not `Services.prefs.*`, in feed and component code. The PrefsFeed is the single bridge.
2. **Bind feed methods on construction.** Pattern: `this.onPrefChangedAction = this.onPrefChangedAction.bind(this);` in the feed's constructor before observers attach.
3. **`init`/`uninit` must be symmetric.** Every observer, listener, or worker spun up in `init` must be torn down in `uninit`. Re-`init` should be safe even after `uninit`.
4. **Pref name constants live in `content-src/lib/PrefsConstants.mjs`** for shared use; widget-scoped prefs may live in the widget's registry module. Don't re-declare the same string literal across components.
5. **System prefs (`*.system.*`) are computed/dynamic; user prefs are user-controlled.** A feature gated by both should evaluate as `systemPref || nimbusVariable` (Nimbus wins when set), and the pref the user toggles in Customize is the user pref, not the system pref.

### Performance & threading
1. **Heavy per-pixel or large-data work belongs in a PromiseWorker,** not on the parent process main thread. Terminate the worker after the one-shot job; don't keep it alive for rare events.
2. **Don't re-fetch what's already in `PersistentCache`.** Cache reads are in-memory after the first load.
3. **Be cautious with `setState` in `componentDidUpdate`** and similar lifecycle hooks; gate updates on actual value changes to avoid render loops.
4. **Avoid `backdrop-filter: blur()`** in newtab styles until performance issues there are resolved; prefer translucent backgrounds.

### Build, bundling, and tooling
1. **JSX/SCSS edits require `./mach newtab bundle`** before the patch is ready for review. The generated `activity-stream.bundle.js` and compiled CSS must be committed in the same patch as their sources.
2. **Don't hand-edit `activity-stream.bundle.js`, `activity-stream.css`, or files under `webext-glue/locales/`.** They are generated.
3. **Per-file coverage thresholds are enforced.** New components need Jest tests sufficient to keep `karma.mc.config.js` thresholds green; add component-stub tests when adding components, even if behavior tests come later.
4. **Sanitize SVG assets through `svgo`** (no editor metadata, no DOCTYPE, lowercase short hex colors, no excessive numeric precision). PNG assets need optimization before landing.
5. **Use `moz-src://` URIs via the newtab `moz-src` helper** for new module imports inside the addon, while keeping a `resource://` fallback for older hosts during the trainhop window.

## Active Campaigns (transient)

### Nova layout migration
The new tab is migrating from the classic responsive layout to the Nova grid system (`nova.enabled` pref). Code paths must work in both modes; new components target Nova first and use `.nova-enabled &` overrides or `@nova-cleanup` markers for legacy support. **Context: likely to fade once Nova graduates and the `nova.enabled` pref is removed.**

### Pocket → Recommended Stories deprecation
Pocket-branded UI, prefs (`extensions.pocket.*`), and telemetry events (Save/Archive/Delete from Pocket, Pocket logged-in CTA) are being removed; "Recommended stories" is the user-facing label. Don't add new Pocket references; remove referenced strings/icons/CSS when removing components. **Context: likely to fade once all Pocket references are stripped.**

### Productivity widgets (Lists / Focus Timer / Weather Forecast / Sports / Clocks)
Widgets share a common container, telemetry shape (`widget_name`, `widget_size`, `action_value`), and size-prefs pattern (`widgets.<name>.size`). New widgets should follow the existing scaffolding: registry constants, feed module, JSX component, customize-panel toggle, unified-telemetry helper. **Context: likely to fade once the widget set stabilizes and the unified telemetry shape ossifies.**

### Settings redesign for Firefox Home
`about:preferences#home` is being restructured into grouped `setting-group`/`moz-box-item` markup with new icons, dropdowns, and migration recipes. Coordinate with `#settings-reviewers` and supply Fluent migrations. **Context: likely to fade once the redesign ships and existing markup is removed.**

## Common Pitfalls

- Editing `activity-stream.bundle.js` or compiled CSS directly instead of bundling.
- Adding a Nimbus feature/variable to `FeatureManifest.yaml` for a behavior that needs to train-hop, instead of using `trainhopConfig`.
- Adding a pref to `firefox.js` and forgetting `ActivityStream.sys.mjs`'s `PREFS_CONFIG`, breaking older hosts.
- Removing a host-side API or string in the same cycle that the XPI starts using it, breaking the trainhop window.
- Hardcoding English strings in JSX, or using a single Fluent ID with `aria-label` instead of `data-l10n-id` + `.aria-label`.
- Mutating Redux state from a render path or returning early before a hook runs, producing React error #310.
- Using physical `left`/`right` properties or non-token padding/margin values; combining two tokens with `calc()`.
- Triggering click handlers on arbitrary keys (Tab, Esc) instead of just Space/Enter; relying on hover-only visibility for context-menu buttons.
- Forgetting to remove observers/listeners in `uninit`, leaking across feed re-inits.
- Asserting against rendered Fluent text in tests, which breaks when localization markers (bidi, accents, pseudolocale) are inserted.
- Sending telemetry from `componentDidMount` rather than via an `IntersectionObserver`, which over-counts preloaded newtab impressions.
- Iterating large image data on the main thread instead of a PromiseWorker.

## File-Glob Guidance

### `browser/extensions/newtab/lib/**/*.sys.mjs` (feeds, services)
- This code train-hops; treat host APIs as feature-detected.
- Bind methods, symmetric init/uninit, read state via the Redux store rather than direct service calls when possible.
- Add `@backward-compat` markers around shims (campaign).

### `browser/extensions/newtab/content-src/components/**/*.jsx`
- Pure presentational + small lifecycle; heavy logic goes in feeds.
- Annotate Nova-only branches with `@nova-cleanup` (campaign).
- New components ship with at least a stubbed Jest test.
- Use design tokens for all spacing/color/typography.

### `browser/extensions/newtab/content-src/**/_*.scss`
- Logical properties only; tokens over literals; no `!important` without a comment.
- Nest `.nova-enabled &` overrides rather than forking files (campaign).
- HCM (`forced-colors`) considered explicitly.

### `browser/extensions/newtab/lib/**/*Feed.sys.mjs` and `lib/Widgets/**`
- Follow the action-handler switch pattern; dispatch through Redux `BroadcastToContent`/`OnlyToOneContent`.
- `init`/`uninit` symmetry; cache reads/writes go through `PersistentCache`.

### `browser/components/newtab/**`, `browser/modules/AboutNewTab*.sys.mjs`, `browser/actors/AboutNewTab*.sys.mjs`
- Host-side: ships with Firefox, does *not* train-hop.
- Changes here require coordinating with the trainhop XPI's expectations.

### `browser/extensions/newtab/webext-glue/metrics/runtime-metrics-*.json`
- One file per supported host version; required for trainhop metric registration.
- Run `./mach lint --fix --outgoing` before submitting; missing `extra_args_types` allowlist entries cause silent registration failures.

### `browser/components/newtab/metrics.yaml`, `pings.yaml`
- Reuse existing categories; share descriptions via YAML anchors.
- Correct `data_sensitivity`; document new fields with `description:` text translators/analysts can read without context.

### `browser/components/preferences/home.*` and related
- Coordinate with `#settings-reviewers` (campaign).
- Provide Fluent migration recipes for renamed/repurposed strings; test with `./mach fluent-migration-test`.

### `toolkit/components/nimbus/FeatureManifest.yaml`
- Adding to top-level features is not train-hop compatible — use `newtabTrainhop` instead unless the feature ships with the host.

### `browser/extensions/newtab/test/**`
- Jest for components, xpcshell for feeds/services, browser-mochitest for end-to-end UI.
- Don't assert against Fluent-rendered text; assert against Fluent IDs and dispatched actions.

## Review Checklist

1. Does any new code under `browser/extensions/newtab/` call a host API that might not exist on the trainhop window's oldest version? If so, is it feature-detected and `@backward-compat`-tagged?
2. Are new prefs defined with defaults in `ActivityStream.sys.mjs` `PREFS_CONFIG`?
3. Are new Nimbus variables routed through `trainhopConfig` rather than added as top-level features?
4. If JSX/SCSS changed, was `./mach newtab bundle` run and the bundle committed?
5. Are user-facing strings in Fluent with comments where intent is ambiguous? Are migrations supplied for renamed strings?
6. For interactive elements: keyboard story (Space/Enter only), correct ARIA, HCM-tested, focus visible?
7. For styles: design tokens (no magic numbers, no two-token `calc`), logical properties, contextual color tokens for wallpaper-aware text?
8. Are observers, workers, and listeners torn down in `uninit`? Is re-`init` safe?
9. Are tests asserting on dispatched actions / metric values / Fluent IDs rather than rendered strings?
10. Are runtime-metrics JSON files updated for any metric/ping change that needs to ride a trainhop?
11. Does any per-pixel / large-data work run on the main thread instead of a PromiseWorker?
12. If this is a Nova-only change, is it gated and `@nova-cleanup`-tagged for later removal?

## House style references

- [CSS Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- [SVG Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/svg_guidelines.html)
- [RTL Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/rtl_guidelines.html)
- [JavaScript Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_js.html)
- [Python Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_python.html)
- [C++ Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_cpp.html)
- [Using C++ in Firefox Code](https://firefox-source-docs.mozilla.org/code-quality/coding-style/using_cxx_in_firefox_code.html)
- [Fluent Localization Tutorial](https://firefox-source-docs.mozilla.org/l10n/fluent/tutorial.html)