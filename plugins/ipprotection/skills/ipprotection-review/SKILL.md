---
name: ipprotection-review
description: Conventions for reviewing patches in browser/components/ipprotection and toolkit/components/ipprotection — covering Lit-based panel components, the IPPService state machine, Fluent strings, telemetry, and proxy/channel filtering.
---

## Standing Conventions

### Architecture & state flow
- Treat `IPProtectionService` / `IPPProxyManager` as the single source of truth for VPN state; UI components must react to dispatched events (`IPPProxyManager:StateChanged`, `IPProtection:Init`, `UsageChanged`, etc.) rather than poll or duplicate state. Keeps state transitions auditable and prevents stale UI.
- Push state mutations through `IPProtectionPanel.setState` (which batches and gates on panel visibility); content components must not mutate `this.state` directly. Avoids divergent renders across windows and keeps content elements declarative.
- Per-window UI (toolbar button, panel, alerts) is created by an `EveryWindow`-style manager; store window references as `Cu.getWeakReference(window)` and expose getters (e.g. `gBrowser`) instead of holding strong refs. Prevents window leaks and matches the project's existing pattern.
- Helper classes (`IPP*Helper`, `IPP*Manager`) own one concern (enrollment, autostart, onboarding flags, alerts, …) and register/unregister observers in matching `init`/`uninit` pairs. New cross-cutting behaviour belongs in a new helper, not in the service or the panel.

### Lit components
- Components live under `content/` as `.mjs` and are pure: props in via attributes/properties, state changes out via bubbling `composed: true` `CustomEvent`s with `IPProtection:*` names. Privileged modules (Services, ChromeUtils, FxAccounts, prefs) must not be imported into content files.
- Use the project's `MozLitElement` query decorators to expose internal nodes (`#myEl`); avoid ad-hoc `shadowRoot.querySelector` from outside the component, and only expose nodes the panel actually needs.
- Slot content from `IPProtectionPanel` / `ipprotection-content` rather than hardcoding child markup inside generic wrappers (e.g. status box, message bar). Style the slotted element with `::slotted()` rather than via the host's own classes.
- Constants shared across components (URLs, max bandwidth, country→flag maps, event names, threshold buckets) live in `content/ipprotection-constants.mjs`. Don't redefine them per component.
- Prefer design tokens (`--space-*`, `--font-size-*`, `--icon-color`, `--border-color-card`, `--color-*`) over hardcoded px/hex values; reach for `light-dark()` or existing themed variables before adding a new one. Hardcoded sizes/colors are a review blocker except where a token genuinely doesn't exist (note it and file follow-up).

### Localization & accessibility
- Every new user-visible string is a Fluent message in `browser/locales/en-US/browser/ipProtection.ftl`, set via `data-l10n-id` / `data-l10n-args` or `document.l10n.setAttributes`. Hardcoded English in components, dialogs, or alerts is a blocker.
- Fluent IDs are lowercase-with-dashes, hardcoded as full strings (no string concatenation to build IDs). Reuse over invent — when meaning changes, mint a new ID rather than mutating an existing one.
- For dynamic numeric content (bandwidth, counts), pass values as `data-l10n-args` and let the message handle plural selectors and `NUMBER`/`DATETIME` formatting. Never assemble numbers + units in JS.
- All toolbar buttons and panel buttons need a tooltiptext or aria-label; XUL `toolbarbutton` uses `.tooltiptext`, HTML/`moz-button` uses `aria-label` or the button's label slot. Verify keyboard navigation (Tab, Shift+Tab, Enter, Space, Arrow keys) and screen reader output before approving UI patches.
- Use logical CSS properties (`margin-inline-*`, `padding-inline-*`, `inset-inline-*`, `border-inline-*`) and `text-align: match-parent` over physical left/right. SVG icons that imply directionality must be mirrored via `:dir(rtl)` or a separate `-rtl` asset; symmetric icons must not be flipped.

### Prefs, telemetry & data
- Prefs live under `browser.ipProtection.*` (camelCase tail), are registered in `firefox.js`, and are documented in `browser/components/ipprotection/docs/`. Use `XPCOMUtils.defineLazyPreferenceGetter` for hot-path reads and `Services.prefs.addObserver` (cleaned up in `uninit`) for change reactions. Don't read prefs from content components — pipe values through panel state.
- Glean metrics live in `metrics.yaml`; new events require a description, the relevant notification emails (including `vpn-telemetry@mozilla.com` for VPN-scoped events), and either a corresponding browser test or an explicit `testing-exception-*` tag with rationale.
- Treat the entitlement and proxy pass as authoritative for bandwidth — derive `max`, `remaining`, and `reset` from the proxy manager's `usageInfo`, never re-implement them from a constant. The cached startup state must be invalidated when sign-in state, entitlement, or `bandwidthUsage` changes.

### Testing
- Use `add_setup` / `registerCleanupFunction` and prefer `SpecialPowers.pushPrefEnv` over manual pref save/restore. Reset the panel via the shared `openPanel` / `closePanel` helpers in `tests/browser/head.js` rather than building bespoke setup.
- Stub external surfaces (`fxAccounts`, `openWebLinkIn`, `GuardianClient` HTTP, `fetchProxyPass`, network observers) with sinon and restore them on cleanup. Don't hit the real network or the real support site in tests.
- Assertions on l10n should compare `getAttributes(el)` to expected `{ id, args }`, not against rendered text. For visibility/state changes that are async, use `BrowserTestUtils.waitForCondition` rather than fixed timeouts.
- Each Phabricator revision must carry either real test coverage or one of the project's `{nav, name=testing-exception-*}` tags with a justification.

## Active Campaigns (transient)

- **Module split — `browser/` → `toolkit/`**: the state machine, proxy manager, channel filter, and network helpers are migrating into `toolkit/components/ipprotection`; window/CustomizableUI/UI helpers remain in `browser/`. New service-layer code should land in `toolkit/`; `browser/`-only APIs (CustomizableUI, EveryWindow, dialogs) must not be pulled into `toolkit/` files. *Context: likely to fade once the toolkit move and the GeckoView abstraction are complete.*
- **State-machine refactor**: `IPPService` and `IPPProxyManager` are converging on an explicit state enum (`READY`, `ACTIVATING`, `ACTIVE`, `PAUSED`, `ERROR`, `NOT_READY`, …) with `#computeState`/`#setState` rather than ad-hoc booleans. New code should drive UI off these states (and `IPPProxyManager:StateChanged`) and avoid adding parallel boolean flags. *Context: likely to fade once all helpers and tests are migrated and the legacy `isActive`/`isError` getters are removed.*
- **Bandwidth & onboarding messaging**: in-panel warnings, infobar warnings, callouts, and the paused dialog are all reading from a shared bandwidth threshold pref + an onboarding bitmask. Use the existing helpers (`IPPOnboardingMessageHelper`, `IPProtectionInfobarManager`, `IPProtectionAlertManager`) and the threshold constants in `ipprotection-constants.mjs`; don't introduce a new place that hardcodes 75/90/100 thresholds. *Context: likely to fade once the messaging surface stabilises post-launch.*

## Common Pitfalls

- Hardcoding bandwidth limits, percentages, or country/flag mappings inline instead of pulling from `ipprotection-constants.mjs` or the entitlement.
- Importing privileged ESMs (Services, ChromeUtils, FxAccounts, PrivateBrowsingUtils) into a `content/*.mjs` Lit component.
- Mutating `this.state` from a content component or from outside `IPProtectionPanel.setState`, causing two windows to disagree.
- Forgetting `composed: true` (or `bubbles: true`) on a `CustomEvent` dispatched from a shadow-DOM component, so `IPProtectionPanel` never sees it.
- Adding event listeners or pref observers in `init` without a matching `removeEventListener` / `removeObserver` in `uninit` (or `disconnectedCallback` for components).
- Comparing rendered Fluent text in tests instead of asserting `data-l10n-id`/`data-l10n-args`; or hardcoding English in `ok`/`is` messages.
- Using `margin-left`/`right`, physical `border-radius` corners, `transform: scaleX(-1)` on text-bearing elements, or omitting `text-align: match-parent` when forcing `direction: ltr` on URL/path fields.
- Calling `Math.floor` / `Math.round` / `toFixed` inconsistently across the panel, infobar, and settings page so the same value renders differently.
- Opening links from a chrome panel via a raw `<a href>` click — use `openWebLinkIn`/`openTrustedLinkIn` (or `moz-support-link` for SUMO) and dispatch an `IPProtection:Close` event when appropriate.
- Adding a new toolbar/panel widget without registering it through `CustomizableUI` and handling `onWidgetRemoved` / overflow (`cui-areatype`, `overflowedItem`, `subviewbutton-nav`) cases.
- Persisting bandwidth, sign-in, or "ever turned on X" state across accounts/profile resets because the relevant pref or cache wasn't cleared on sign-out / entitlement change.
- Logging or asserting on `console.log` left in tests; missing `sandbox.restore()` / stub cleanup.

## File-Glob Guidance

- `browser/components/ipprotection/content/*.mjs` — Lit components only. No privileged imports, no direct pref reads, no global side effects at module top level. Expose nodes via query decorators; emit `IPProtection:*` events for the panel to handle.
- `browser/components/ipprotection/content/*.css` — Use design tokens; logical properties only; gate stylelint exceptions explicitly via `stylelint-rollouts.config.js` rather than scattering disable comments. Match the `panelUI-shared` token names where the panel embeds standard chrome chrome.
- `browser/components/ipprotection/IPProtection*.sys.mjs` — Window/CustomizableUI/EveryWindow glue. Bind `handleEvent` once in the constructor, weak-ref windows, and never reach into a content component's shadow DOM directly.
- `toolkit/components/ipprotection/IPP*.sys.mjs` — Cross-platform service, proxy manager, channel filter, network observers. Must stay free of `browser/`-only modules (CustomizableUI, gBrowser, dialog helpers). State changes are dispatched as events on the singleton.
- `browser/components/ipprotection/assets/**/*.svg` — Run through svgo/SVGOMG; use `context-fill` / `context-stroke` and `-moz-context-properties` so icons follow `--icon-color`. No editor metadata, no hardcoded brand colors.
- `browser/locales/en-US/browser/ipProtection.ftl` — Lowercase-dashed IDs, comments above each message giving developer context; group by panel surface. New IDs require fluent-reviewers approval.
- `browser/components/ipprotection/metrics.yaml` — All new events get `vpn-telemetry@mozilla.com` plus the module owner on `notification_emails`, and a bug link in `bugs`. Prefer `counter`/`event` with typed `extra_keys` over free-form strings.
- `browser/components/ipprotection/tests/{browser,xpcshell}/**` — Use the shared `head.js` helpers (`openPanel`, `setPanelState`, `triggerPausedState`, `DEFAULT_SERVICE_STATUS`); add new helpers there rather than copy-pasting setup. Stub network and FxA. Clear all VPN prefs in `registerCleanupFunction`.
- `browser/components/ipprotection/docs/**` — New states, error codes, prefs, and helpers must be reflected here in the same patch.

## Review Checklist

- [ ] Service/UI separation respected: content stays declarative, privileged work stays in `*.sys.mjs`, and toolkit code stays platform-agnostic.
- [ ] State changes go through `setState` / `#setState`; events use `IPProtection:*` / `IPPProxyManager:*` names with `bubbles: true, composed: true` where they cross shadow DOM.
- [ ] Every `init`/observer/event listener has a matching teardown; weak window refs where applicable; no leaked sandboxes/stubs in tests.
- [ ] All new strings are Fluent with stable lowercase-dashed IDs and developer comments; `data-l10n-args` used for variables; no English literals in JS.
- [ ] Logical CSS properties and design tokens used; RTL spot-checked; HCM border/outline still visible (no reliance on `box-shadow` for focus).
- [ ] Toolbar/panel widget changes handle creation, overflow menu, removal, multi-window, and CustomizableUI placement restoration.
- [ ] Prefs registered in `firefox.js`, documented under `docs/`, read via lazy pref getter or observer with cleanup; no content-side pref reads.
- [ ] Bandwidth/entitlement values come from `IPPProxyManager.usageInfo` / startup cache; rounding and unit display match the rules in `ipprotection-constants.mjs` and other surfaces.
- [ ] Telemetry: `metrics.yaml` updated with description, bug, and `vpn-telemetry@mozilla.com`; tests cover the new event or a `testing-exception-*` tag explains why.
- [ ] Tests use shared helpers and stubs; assert on `data-l10n-id`/state rather than rendered text; clean up prefs, permissions, and stubs.
- [ ] No hardcoded support URLs — use `app.support.baseURL` + a slug from constants, or `moz-support-link`.
- [ ] Patch description carries a clear test plan and the appropriate `{nav, name=testing-*}` tag.

## House style references

- [CSS Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/css_guidelines.html)
- [SVG Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/svg_guidelines.html)
- [RTL Guidelines](https://firefox-source-docs.mozilla.org/code-quality/coding-style/rtl_guidelines.html)
- [JavaScript Coding Style](https://firefox-source-docs.mozilla.org/code-quality/coding-style/coding_style_js.html)
- [Fluent for Firefox Developers](https://firefox-source-docs.mozilla.org/l10n/fluent/tutorial.html)