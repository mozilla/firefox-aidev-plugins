---
name: ipprotection-review
description: Durable review guidance for Firefox's built-in IP Protection (VPN) module, covering panel UI, proxy/channel filtering, authentication, telemetry, and localization.
---

# Module Scope

- Paths: `browser/components/ipprotection/**/*`, `toolkit/components/ipprotection/**/*`
- Bugzilla components: Firefox::IP Protection

# Core Reviewers

- Owner: fchasen
- Peers: kpatenio, rking, niklas

# Standing Conventions

## State & Data Flow
- Route state mutations through `IPProtectionPanel.setState({...})` rather than having child components mutate panel state directly; keep `IPProtectionPanel` as the single source of truth for panel state, and prefer batched `setState` calls over property-by-property assignment.
- Prefer communicating across components via `CustomEvent` dispatched from the shared root and consumed by the panel/manager, rather than sharing state between sibling files. Use `Services.obs` observers (e.g. `perm-changed`) instead of calling into internal callbacks when the platform already emits the signal.
- When adding/removing `addObserver`/`removeObserver` or `addEventListener` pairs, bind the handler once in the constructor (or use `handleEvent`) — do not pass `.bind(this)` at registration time, since the two bindings won't match on removal.

## Constants, Prefs & Magic Numbers
- Centralize shared values (bandwidth thresholds, max bandwidth, support URLs, pref names) in `ipprotection-constants.mjs` or the relevant `*Helpers.sys.mjs`, and import them everywhere they're referenced. Literals like `50`, `150`, `0.75`, `0.9` in component code or Fluent strings are review-blocking.
- Pass user-visible numeric values (bandwidth caps, remaining usage) through Fluent `$variables`; never hardcode units or amounts inside `.ftl` messages. Units (`MB`, `GB`) must be hardcoded into the message text, not passed as variables, since localizers translate them differently.
- Every new pref should be documented under `browser/components/ipprotection/docs/Preferences.rst` (or the toolkit equivalent) with correct type.

## Localization
- Any semantic change to a Fluent string requires a new ID and a Fluent migration under `python/l10n/fluent_migrations/` so translations aren't lost. Dropping an old ID is a separate, deliberate step once no callers remain.
- Don't hardcode country or region names; use `Intl.DisplayNames` / `Services.intl.DisplayNames` and a single parameterized string.
- Fluent comments attach only to the immediately following message — copy the comment for each message that needs it, and use standalone/group comments appropriately.
- New user-facing strings belong in `browser/locales/en-US/browser/ipProtection.ftl` and must be wired into `browser.xhtml` outside the "Untranslated FTL" block.

## Panel UI, Theming & Accessibility
- Use design-system tokens (`--space-*`, `--border-color-card`, `--icon-color`, `--font-weight-*`, `--dimension-*`) instead of raw pixel values or hardcoded colors; SVG assets that need theming must use `context-fill` / `context-stroke` and let CSS set the color.
- Prefer logical properties (`padding-block-*`, `padding-inline-*`, `margin-block-*`) so layouts work in RTL. Any directional glyph (`arrow-right`, etc.) or hand-rolled class like `left`/`right` is a red flag.
- Reuse existing shared icons under `toolkit/themes/shared/icons/` before adding new SVGs; optimize any new SVG (e.g. via SVGOMG) and place module illustrations under `browser/components/ipprotection/assets/` (not `browser/base/content/logos/`).
- Prefer `moz-button` / `moz-card` and existing panel conventions (`subviewbutton-nav`, overflow attributes) over re-implementing styles; avoid overriding `--arrowpanel-*` variables when a local margin/padding change will do.
- Toolbar-button state must not rely on `overflows="true"` to detect overflow — check `overflowedItem="true"` or `cui-areatype="panel"` (or set `subviewbutton-nav` at creation time).
- Keyboard focus, screen-reader announcements, and HCM outlines are required for every new interactive element. For toggles and buttons inside the panel, verify the accessible name and pressed state with NVDA/VoiceOver/Orca before r+.

## Testing
- Manage prefs in tests with `SpecialPowers.pushPrefEnv`; it auto-reverts on teardown, so don't add manual `clearUserPref` cleanup for prefs it set.
- Do not use `TestUtils.waitForCondition` to await things that can be observed deterministically; resolve a promise from inside the stub/handler you care about. This is a 100 ms-per-check polling cost that compounds across CI.
- New panel/state/service behavior needs a corresponding `browser/xpcshell` test. Use the project tag `testing-approved`, or one of the documented exceptions with a one-line justification, on every revision.
- When stubbing manager state, use the existing patterns in `browser_ipprotection_*` tests (e.g. `sandbox.stub(IPPProxyManager, "state").value(...)`) and `setupVpnPrefs` / `cleanupStatusCardTest` helpers rather than reinventing setup.

## Data Collection
- Any change touching `metrics.yaml` must carry a `#data-classification-*` tag with a one-line justification, and the `data_sensitivity` property must match. Add `vpn-telemetry@mozilla.com` to `notification_emails` for new IPP metrics.
- Prefer `counter`/`event` metrics over bespoke aggregation; record state transitions (e.g. "was active before pause") rather than current state when the event already implies it.

## Proxy & Channel Filtering
- When excluding a channel from IPP, pass through `defaultProxyInfo` to `onProxyFilterResult` — never `null` — so the user's system proxy is honored.
- Prefer `nsIIOService::hostnameIsLocalIPAddress` (and related platform APIs) over regex for IP/host classification.
- Lifecycle pairing: any code path that starts a channel filter, connection, or abort controller must have a matching teardown (`cancelChannelFilter`, `stop`, abort reason) in every exit path, including error and paused transitions.

# Active Campaigns (transient)

- **Move IPP into `toolkit/`**: New non-UI logic (state machine, proxy manager, guardian client, auth provider) should land in `toolkit/components/ipprotection/` and avoid depending on desktop-only singletons (`CustomizableUI`, `EveryWindow`, etc.); platform-specific glue lives under `fxa/` or `android/` subdirs. Context: likely to fade once the Android/Fenix integration is fully wired up and the `browser/` → `toolkit/` migration is complete.
- **Auth provider abstraction**: New FxA/Guardian code should go through `IPPAuthProvider` rather than reaching into `GuardianClient` singletons; avoid introducing cycles between `IPPService` and auth helpers. Context: likely to fade once the provider refactor lands and stabilizes.
- **Bandwidth rounding consolidation**: Remaining/used bandwidth is currently rounded in several places (`bandwidth-usage`, `ipprotection-content`, `IPProtectionInfobarManager`); new callers should factor through a shared helper rather than re-implementing `Math.floor` / `toFixed` logic. Context: likely to fade once a single rounding utility is extracted.

# Common Pitfalls

- Using `Math.floor` for remaining bandwidth where UX expects one-decimal precision (notably at the 75% bucket), or inverting the progress bar by binding it to `remaining` instead of `used`.
- Dispatching events from one component while mutating the same state property directly in another, leading to drift between the panel and child components.
- Adding a new button/toggle without wiring `data-l10n-id` accessibility attributes, or duplicating an aria-label that's already provided by `tooltiptext`.
- Firing an ASRouter trigger unconditionally and encoding the gating logic in JS, instead of passing context properties and letting `targeting` decide.
- Adding feature callouts without the `cfr` group, without `previousSessionEnd`, or without `!hasActiveEnterprisePolicies && !activeNotifications`. Omitting `dismiss: true` on CTA button actions.
- Landing a permanent promotional message in-tree without a `lifetime` frequency cap and without considering a Nimbus rollout for safe kill-switching.
- Starting an abort controller / channel filter but not clearing it on every exit path (error, paused, stop-while-activating).
- Creating new icon SVGs that duplicate existing ones in `toolkit/themes/shared/icons/`; placing state illustrations in `browser/base/content/logos/`.
- Forgetting the Fluent migration when renaming a user-facing string ID, or leaving the old ID around after all call sites are updated.
- Running `mach lint` failures (fluent-lint, eslint, stylelint, file-whitespace) through to review; these should be clean before requesting review.
- Editing `mots.yaml` without running `mots clean`.

# File-Glob Guidance

- `browser/components/ipprotection/content/*.mjs` — Components must read from `this.state` populated by `IPProtectionPanel`; they should dispatch `CustomEvent`s upward rather than mutating panel state. Use logical CSS properties and design tokens.
- `browser/components/ipprotection/IPProtection*.sys.mjs` — Panel/manager/alert code owns state mutations and pref observers. Prefer `setState` batching; document new prefs in `docs/Preferences.rst`.
- `toolkit/components/ipprotection/**` — Keep cross-platform-safe (no `CustomizableUI`, `EveryWindow`, `browser/`-only imports). Platform-specific glue goes in `fxa/` or `android/` subdirs (campaign).
- `browser/components/ipprotection/IPPChannelFilter.sys.mjs` — Always pass `defaultProxyInfo` through to excluded channels; store it alongside pending channels so reprocessing preserves it.
- `browser/components/ipprotection/content/*.css` + `browser/themes/shared/**` — Use design tokens and logical properties; prefer `.toolbarbutton-icon` over raw `image`; reuse `subviewbutton-nav` for subview arrows.
- `browser/locales/en-US/browser/ipProtection.ftl` — New/changed IDs require a migration. Pass numbers as `$variables`; hardcode units. Comments attach only to the next message.
- `browser/components/asrouter/modules/FeatureCalloutMessages.sys.mjs` — New callouts belong in the `cfr` group with `previousSessionEnd`, `!hasActiveEnterprisePolicies && !activeNotifications`, and `dismiss: true` on CTA buttons.
- `**/metrics.yaml` — New metrics need data-classification tag, matching `data_sensitivity`, and `vpn-telemetry@mozilla.com` in notifications.
- `browser/components/ipprotection/tests/**` — Prefer `SpecialPowers.pushPrefEnv` and promise-resolving stubs over `waitForCondition`; reuse existing `head.js` helpers.
- `browser/components/ipprotection/docs/**` — Keep `StateMachine.rst`, `Preferences.rst`, `Constants.rst`, `Components.rst` in sync with code changes in the same patch.

# Review Checklist

- [ ] `mach lint --outgoing` clean (eslint, stylelint, fluent-lint, file-whitespace, rejected-words).
- [ ] State mutations go through `setState`; no cross-file direct state writes.
- [ ] No magic numbers for thresholds/caps/URLs — constants imported from the shared module.
- [ ] New/changed Fluent IDs have a migration; units hardcoded; numbers passed as `$variables`.
- [ ] New prefs documented in `docs/Preferences.rst` and use matching constants in code.
- [ ] SVGs use `context-fill`/`context-stroke`; tokens (not pixel literals) drive spacing and color; logical properties used.
- [ ] Accessibility verified: accessible name, pressed/toggled state, keyboard focus, HCM outlines.
- [ ] Lifecycle balanced: every start/addObserver/addEventListener/AbortController has a matching teardown on all paths.
- [ ] Tests use `pushPrefEnv` and promise-based stubs; no `waitForCondition` unless truly necessary; testing-policy tag applied.
- [ ] `metrics.yaml` changes carry a data-classification tag and correct `data_sensitivity`; notification emails include `vpn-telemetry@mozilla.com`.
- [ ] Docs (`StateMachine.rst`, `Components.rst`, etc.) updated in the same patch when behavior changes.
- [ ] `mots.yaml` run through `mots clean` if touched.