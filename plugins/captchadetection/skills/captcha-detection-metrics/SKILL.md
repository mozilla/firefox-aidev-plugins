---
name: captcha-detection-metrics
description: >-
  Interpreting and querying Firefox's `captcha_detection.*` Glean metrics and the
  `captcha-detection` custom ping (BigQuery `mozdata.firefox_desktop.captcha_detection`,
  `mozdata.fenix.captcha_detection`). Use when analyzing captcha prevalence or solve /
  pass / interacted rates per vendor (ArkoseLabs, Cloudflare Turnstile, Datadome,
  reCAPTCHA v2, hCaptcha, AWS WAF), cohorting the ping by privacy settings or browsing
  volume, or writing or reviewing a query or dashboard over it. Records which ratios are
  valid per vendor, which counters are dead or over-counting, and the filters that keep
  non-organic rows out.
---

# Analyzing the CAPTCHA detection metrics

## Introduction

Context and guidance for analyzing the `captcha_detection.*` metrics defined in
`metrics.yaml` and sent in the `captcha-detection` custom ping (`pings.yaml`).
Everything lives in `toolkit/components/captchadetection/` in mozilla-central:
`CaptchaDetectionChild.sys.mjs` (detects captchas in-frame),
`CaptchaDetectionParent.sys.mjs` (records metrics),
`CaptchaDetectionPingUtils.sys.mjs` (ping submission). File paths below are
relative to that directory unless stated otherwise.

Purpose (per `pings.yaml`): analyze how often CAPTCHAs appear in the wild, broken
down by users' anti-tracking / anti-fingerprinting settings. This document is
about *interpreting and querying* the data — it records the non-obvious things
that are easy to get wrong.

The ping is **captcha-triggered**: it is submitted when a client encounters a
detected captcha (an outcome event flags unsubmitted data; `pages_visited` alone
does not trigger submission). It is therefore NOT sent by every client — the
reporting population is "clients who hit a detected captcha", which is the right
denominator to keep in mind when sizing any analysis.

Detection is DOM/heuristic based: an in-frame actor identifies a vendor's captcha
and reports load and outcome events, which the parent turns into counters. The
exact triggers are vendor-specific (see Metrics Overview). Because detection
depends on the vendor's page structure, it can miss cases the heuristic doesn't
match, and a trend change can reflect a vendor markup change rather than user
behavior.

## Metrics Overview

The ping carries, per client:

- **Per-vendor counters** for each supported captcha provider (below). Every
  counter has a normal and a `_pbm` (Private Browsing Mode) variant, with one
  historical exception: `datadome_oc_pbm` was only added in Firefox 154 (bug
  2054037). It is NULL, not 0, on submissions from older builds — including
  current ESR — so any window reaching back before 154 must treat it as
  missing rather than as a zero load count (see Datadome).
- **Context metrics** recorded at collection time: `privacy_*` (tracking
  protection incl. cryptomining/known-fingerprinter toggles, fingerprinting
  protection, resistFingerprinting) and `network_cookie_*` (cookie behavior,
  opt-in partitioning). These describe the user's settings, not captcha events.
- **`pages_visited`** (+ `_pbm`) — a browsing denominator.

Counter-suffix legend: `oc` loaded, `ps` shown, `pc`/`cc` passed/completed,
`pf`/`cf` failed, `ac` auto-completed, `bl` blocked. **Not all vendors record all
suffixes** — see each subsection. Pair non-`_pbm` counters with `pages_visited`
for normal browsing and `_pbm` counters with `pages_visited_pbm` for private
browsing; never mix the two.

**Counters are batched across pings, so a single ping can look inconsistent.** The
ping accumulates counters and submits periodically (`CaptchaDetectionPingUtils`,
~once/24h), not once per captcha. A captcha's lifecycle can straddle a submission
boundary: the widget loads (incrementing `oc`) before a ping is sent, and the user
interacts / it resolves (`ps`/`ac`/`cc`/`cf`/`pc`/`pf`) only after — so the load
lands in one ping and its outcome in the next (or an outcome lands in a ping whose
load already shipped). Within a single ping you can therefore see an outcome with
no matching load, or a load whose outcome never arrives, and a per-ping ratio can
exceed 100%. These straddles are small and mostly cancel in aggregate; a *large*
imbalance (an outcome far exceeding its load count) instead signals corrupt /
non-organic data — which is why the invalid-ratio checks (Data Analysis
Techniques) use a gross tolerance rather than a strict inequality.

### ArkoseLabs
Counters:

- `arkoselabs_oc` — an Arkose puzzle loaded (the game-like "FunCaptcha"). There's
  no checkbox to click first, so a load basically means the puzzle appeared.
- `arkoselabs_pc` — the puzzle was solved (the Arkose server confirmed "correct").
- `arkoselabs_pf` — the puzzle was gotten wrong (the server said "wrong").
- `arkoselabs_solutions_required` — how many rounds ("waves") that one puzzle made
  the person do. Stored as a spread of values, not a single number.

`pc`/`pf` come from a network-response observer on the Arkose API (`/fc/ca/`):
the terminal `solved` boolean -> `pc` (true) or `pf` (false). **Arkose has a real
`pf` fail counter**, so `pc/(pc+pf)` is a genuine solve rate (not a lower bound
like the widget vendors).

NOTE: `arkoselabs_ps` exists in the schema but is **never recorded (always 0)** —
nothing in the code increments it. Ignore it. Also `solutions_required.count` is
the deprecated internal field (bug 1799509, unpopulated) — the sample count is
`pc + pf`, so mean rounds = `solutions_required.sum / (pc + pf)`.

**Ratios (normal browsing):**

- prevalence = `oc / pages_visited` (~0.0043%) — how often an Arkose puzzle shows
  up, out of all the pages people load.
- **solve rate = `pc / (pc + pf)`** (~67%) — of the puzzles that got a clear
  win-or-lose answer, the share that were solved. This is the number to trust,
  because wins and losses are counted the same way.
- completion = `(pc + pf) / oc` (~34%) — ArkoseLabs's version of the **interacted**
  (resolved) rate the other providers have; the dashboard groups it in the
  *Interacted* section. Of the puzzles that loaded, how many we actually saw end
  in a win or a loss. Only rough: people leave or close the tab, and we don't
  always catch the ending.
- mean solutions required = `solutions_required.sum / (pc + pf)` (~2.26) — how
  many rounds a typical puzzle asks for.
- Sanity check: wins + losses can't be more than loads (`pc + pf <= oc`), give or
  take the rare edge case.

NOTE: `solutions_required` counts **waves within a single challenge, not retries**.
FunCaptcha shows several image "waves" in sequence; the response observer counts
each `/fc/ca/` wave and, when a terminal `solved` boolean arrives, records one
`pc`/`pf` plus that accumulated wave-count, then resets. So the mean-rounds figure
(~2.26) and the solve rate are **independent**: a 2-wave challenge is still ONE
session ending in ONE outcome, and the waves are not themselves pass/fail events —
so "avg ~2 waves" does NOT imply a ~50% solve rate. The ~67% solve rate means
~33% of *decided* challenges came back `solved=false` (genuine, server-confirmed
fails); abandoned challenges never get a terminal boolean, so they are excluded
from both `pc` and `pf` (this is why the solve rate is a true rate, not a lower
bound like the widget vendors).

### AWS WAF — defined but DEAD (do not use)
Counters (all scaffolded, never wired up):

- `awswaf_ps`
- `awswaf_pc`
- `awswaf_pf`
- `awswaf_solutions_required`

They exist in the schema / Glean dictionary, but there is no AWS WAF handler or
recording code (not in this tree, not in searchfox/mozilla-central), and the
production table carries **zero data** for all of them over 90 days (verified:
`max(awswaf_ps)=0`, no rows > 0). No ratios are computable. Treat as absent until
an implementation lands; a cleanup bug to either implement or remove these metrics
would be reasonable.

### Cloudflare Turnstile
Counters:

- `cloudflare_turnstile_oc` — a Turnstile challenge loaded on the page. Turnstile
  usually checks you in the background, so a load does NOT mean the person did
  anything.
- `cloudflare_turnstile_cc` — the challenge ended in a pass (the green check).
  This includes passes that happen automatically with no clicking.
- `cloudflare_turnstile_cf` — the challenge ended in a fail.

What they mean — the child actor (`CaptchaDetectionChild.sys.mjs`):

1. Identifies a Turnstile challenge iframe by its URL and constructs a handler
   -> increments `..._oc`.
2. Watches the widget's shadow DOM for a `#success` / `#fail` div to become
   visible -> increments `..._cc` or `..._cf`. The observer disconnects after
   the first outcome, so **at most one `cc`/`cf` per `oc`**.

`oc` fires when the challenge iframe loads (the handler is constructed on the
iframe-URL match), independent of visibility: a Turnstile that never surfaces a
`#success`/`#fail` div (invisible/managed mode, or torn down before it shows)
yields an `oc` with no `cc`/`cf` outcome. Crucially, the handler only
checks *which of* `#success`/`#fail` is displayed — there is **no interaction
detection at all**. A managed / non-interactive Turnstile that passes on its own
(the success checkmark appears with zero user action) increments `cc` identically
to a pass the user actually worked through. So **`cc` is not evidence of user
interaction**, and Turnstile records only `oc`/`cc`/`cf` (no `ps`/`ac`) — automatic
and interactive passes cannot be distinguished. This gap is tracked in **bug
2054267** (under meta 2054266): add a Turnstile auto-vs-interactive signal so it
can be segmented like reCAPTCHA/hCaptcha.

Appropriate ratios (`oc`/`cc`/`cf` are separate counters at different lifecycle
points — do NOT use raw `cc/oc` as a "solve rate"):

- **Pass rate = `cc / (cc + cf)`** — of the challenges we actually saw finish
  (pass or fail), the share that passed. This is the cleanest "did it succeed"
  number, and it's always between 0 and 100%. Show `cc+cf` next to it, and don't
  trust it when only a handful of challenges finished.
- **Interacted = `(cc + cf) / oc`** — of the Turnstiles that loaded, how many we
  saw finish at all. The rest never showed a pass or fail (they ran in the
  background, got closed, or our detector missed them) — that is NOT the same as
  the person "giving up." Despite the name, this is really "how many resolved",
  NOT "a human interacted": Turnstile often passes on its own, and those silent
  passes still count as `cc`.
- **Prevalence = `oc / pages_visited`** — how often a Turnstile loads per page.
  Very small (around 0.005%). Good for "how common is Turnstile".
- Don't use **`cc / oc`** as a "solve rate" — it mostly reflects how often
  Turnstile runs in the background, not whether people succeed.

Caveat: pass rate is bounded 0-100% by construction; `Interacted`/`Prevalence`
are not bounded at daily granularity (see the invariant under Data Analysis).

### Datadome
Counters:

- `datadome_oc` — Datadome stepped in with its full-page gate screen. This only
  fires when Datadome actually interrupts the person, not just because the site
  uses Datadome.
- `datadome_ps` — that screen showed a puzzle to solve.
- `datadome_pc` — the puzzle was passed.
- `datadome_bl` — the person was hard-blocked (a "no entry" page, no puzzle to
  even try).

Recording (`recordDatadomeEvent`): a load reports `ps` (puzzle) or `bl` (hard
block) — mutually exclusive; a pass reports `pc`. So `ps + bl <= oc`, `pc <= ps`.
There is **no auto-success** signal (a silent pass loads no interstitial).
`datadome_oc_pbm` was missing until bug 2054037 added it in **Firefox 154**, so
PBM *load* data only exists from 154 onward (older builds, current ESR included,
report PBM `ps`/`bl`/`pc` but no `oc`). On those older submissions the column is
NULL rather than 0, so a PBM prevalence denominator built from it silently drops
them instead of dividing by zero — scope any `oc_pbm` ratio to 154+ explicitly.

**Ratios (normal browsing):**

- intervention prevalence = `oc / pages_visited` — how often Datadome interrupts
  someone per page (it actually stepped in, not just "the site uses it").
- block share = `bl / (ps + bl)` — when Datadome steps in, how often it's a
  flat-out block versus a puzzle you can actually solve (~27%). The main Datadome
  number.
- solve rate given puzzle = `pc / ps` — of the puzzles shown, how many got passed.
  This is a floor, not the true rate: there is no "failed" counter, the pass can
  go uncounted if the page moves on, and lots of people just leave the site — all
  of which look like "not solved."
- block exposure = `bl / pages_visited` — how often someone gets hard-blocked per
  page. A direct "how much does this hurt people" measure.

Dropped as redundant (since `ps + bl ≈ oc`): puzzle share (= 1 − block share) and
puzzle non-completion (= 1 − solve rate).

### Google reCAPTCHA v2
Counters:

- `google_recaptcha_v2_oc` — the "I'm not a robot" checkbox loaded on the page.
  (Only the visible checkbox kind; the fully-invisible kind isn't counted.) It
  fires when the box loads, not when someone clicks it — so most of these are just
  sitting on the page, unused.
- `google_recaptcha_v2_ps` — the person was shown an image puzzle ("pick all the
  buses").
- `google_recaptcha_v2_pc` — that image puzzle was solved.
- `google_recaptcha_v2_ac` — the person was waved through with no puzzle at all.

Recording (`updateGRecaptchaV2State`): `ImagesShown` -> `ps`; a
checkmark -> `ac` if images were never shown, else `pc`. Per widget `ac` and `ps`
are meant to be mutually exclusive with `pc <= ps` and `ac + ps <= oc` — but in
release data **`ps` grossly over-counts** (see the "shown" note below), so
`ac + ps <= oc` does NOT hold in practice. **No fail counter.**
Interactions = `ac + ps`.

**Ratios (normal browsing):**

- loaded per page = `oc / pages_visited` — how often the checkbox loads per page.
- interacted per page = `(ac + ps) / pages_visited` (or `(ac + ps) / oc` per load)
  — how often something actually happened with it (a wave-through or a puzzle).
  Most loaded boxes never get this far.
- auto-success % of interactions = `ac / (ac + ps)` — of the boxes that did
  something, how many waved the person through with no puzzle.
- success rate (challenged) = `pc / ps` — of the puzzles shown, how many got
  solved.
- non-completion rate (challenged) = `(ps - pc) / ps` — the flip side: fails and
  give-ups lumped together (there is no separate "failed" counter).

**Cross-provider caveat (validated against 90d release data, desktop + Android):** `pc/ps` is a
within-provider **lower bound**, not a clean solve-success rate, and is **not
comparable across providers**. The observed ~43% (reCAPTCHA) vs ~94% (hCaptcha)
is NOT relative solve skill; two things drive it:

- **`pc` loss + abandonment (the main driver):** the post-solve checkmark (`pc`)
  is often lost when solving submits the form / navigates away before it is
  recorded, and reCAPTCHA's multi-round image puzzles are genuinely abandoned more
  than hCaptcha's. Both push reCAPTCHA's `pc/ps` down (measurement + behaviour).
- **Different definitions of "shown":** reCAPTCHA `ps` fires on challenge-element
  *existence* (`rc-imageselect` present in the bframe); hCaptcha `ps` fires on
  *visibility* (`aria-hidden` flips). reCAPTCHA's existence check **does
  over-count**, confirmed in 90d release data: `ps` re-fires on the persistent
  element, reaching **76,156 in a single ping** and pushing `ac + ps > oc` for
  ~165k clients (~0.4%). Being fixed / aligned in **bug 2054272** (under meta
  2054266). `ps` is also interaction-gated — only ~1.6% of `oc` — so it does NOT
  mean "the widget was present"; it means a challenge was *instantiated for an
  engaged user*.
Separately, `oc` counts widget *loads*: reCAPTCHA sits on ~6% of pageviews with
only ~2.4% ever interacted (passive embeds / periodic token-refresh reloads), so
oc-denominated ratios mean "widget present", not "user challenged". (That passive
majority shows up in the *interacted* rate, not in `pc/ps` — ignored widgets never
reach `ps`.)

### hCaptcha
Counters:

- `hcaptcha_oc` — the hCaptcha checkbox loaded on the page. Like reCAPTCHA, this
  fires at load, not when someone actually uses it.
- `hcaptcha_ps` — the person was shown the puzzle.
- `hcaptcha_pc` — the puzzle was passed.
- `hcaptcha_ac` — the person was waved through with no puzzle.

Same recording model and mutual exclusivity as reCAPTCHA v2; no
fail counter. Unlike reCAPTCHA, hCaptcha `ps` fires when the challenge frame
becomes **visible** (`aria-hidden` -> false) — a tighter "genuinely shown"
denominator that does not have reCAPTCHA's existence over-count (max `ps` per ping
~400, not ~76k), so `ac + ps <= oc` holds far more tightly. That, plus hCaptcha being deployed as hard gates
(~43% of loads are interacted vs reCAPTCHA's ~2.4%), is why its `pc/ps` runs ~94%:
a measurement + deployment difference, not that hCaptcha is "easier" to solve.

**Ratios (normal browsing):** identical
shape to reCAPTCHA v2 with the `hcaptcha_` prefix — loaded/page `oc/pages`,
interacted/page `(ac+ps)/pages`, auto-success% `ac/(ac+ps)`, success `pc/ps`,
non-completion `(ps-pc)/ps`.

## Known metric gaps (tracked)

Improvements to these metrics are tracked under meta **bug 2054266**:

- **bug 2054267** — Cloudflare Turnstile cannot distinguish automatic from
  interactive passes (`cc` counts silent auto-passes; no `ac`/`ps`).
- **bug 2054272** — reCAPTCHA `ps` uses element *existence* while hCaptcha uses
  *visibility*; investigate and align so "shown" means the same across providers.
- AWS WAF metrics are scaffolded but dead (see above) — implement or remove.

Keep these in mind when comparing providers: the counters were not all designed
to the same definition.

## Data Analysis Techniques

Ratios are provider-specific (see Metrics Overview). Independent of provider, the
techniques below control *which rows* enter the numerator/denominator. Always
pair a counter with the matching-mode `pages_visited` and report the denominator
count so small samples are visible.

### Cohorts by privacy settings (composite key)
Build a composite key from the `privacy_*` / `network_cookie_*` context metrics
and treat each distinct combination as a cohort. Split into a **non-PBM key**
(the non-`_pbm` settings, paired with non-PBM counters) and a **PBM key** (the
`_pbm` settings plus the settings that have no PBM variant — cookie behavior,
cryptomining/known-fingerprinter protection — which apply in both modes, paired
with `_pbm` counters).

Suggested selection rule: include any combination with **> 10,000 reporting
clients on each of the last 7 days straight** (release, non-bot). Firefox
settings are overwhelmingly at their defaults, so a handful of profiles cover
almost the whole population; everything else is long-tail. Typical profiles:

- **ETP Standard** — the release default (tracking-protection toggle off;
  cryptomining + known-fingerprinter protection on; Total Cookie Protection).
- **ETP Strict** — fingerprinting protection + tracking protection on.
- **PBM** — the private-browsing defaults, evaluated on the PBM key.
- **RFP** — `resistFingerprinting = true`, any other setting. A tiny hardened
  cohort added explicitly; usually too small for reliable rates.
- **Other** — the non-PBM catch-all: any combination that is not one of the named
  profiles above (custom configs, plus pings with unset / partial prefs). Not a
  single setting; keep it as a **coverage meter** — how much normal-browsing
  traffic isn't a named default.
- **Other (PBM)** — the same catch-all on the PBM key: private-browsing pings that
  don't match the PBM default. Coverage meter for the private-browsing population.

**Composite values are platform-specific — do not port desktop composites to
Android (or vice versa).** The same conceptual profile serializes to different
booleans per platform because the products have different defaults and report
some settings differently. Known differences (Firefox for Android / Fenix vs
desktop):

- **PBM default differs by one flag:** Android reports
  `trackingprotection_pbm_enabled = false` where desktop reports `true`. So the
  desktop PBM key matches ~0 Android clients; Android's PBM default is otherwise
  identical (`rfp_pbm=false, fpp_pbm=true, tp_pbm=false, optin_pbm=false,
  cryptomining=true, known-fp=true, cookieBehavior=5`).
- **ETP Standard** matches the same composite on both platforms.
- **ETP Standard vs Strict is NOT distinguishable on Android from this ping.**
  Verified by cross-tabbing per client against
  `preferences.enhanced_tracking_protection` (the Fenix `metrics` ping, the
  ground-truth mode): **99.4% of true Strict users report `fpp=false`** — the
  same composite as Standard
  (`rfp=F, fpp=F, tp=F, crypto=T, fp=T, cookie=5, optin=F`). True Strict is
  ~2.46% of Fenix release (~830k clients, comparable to desktop), but the
  captcha ping records them as Standard. ROOT CAUSE (confirmed in source): this
  metric reads the pref `privacy.fingerprintingProtection`; GeckoView's engine
  setting maps to that same pref, but Fenix sets it AT ENGINE CREATION from a
  Nimbus rollout, not from ETP mode. In `Core.kt` the engine default is gated
  on the Nimbus feature:
  `if (FxNimbus.features.fingerprintingProtection.value().enabled) { defaultSettings.fingerprintingProtection = ...enabledNormal }`.
  The ETP-Strict->FPP wiring only runs transiently on the settings screen
  (`TrackingProtectionFragment.updateFingerprintingProtection()`). So on
  Android `fpp` tracks the FPP Nimbus experiment, NOT the ETP Standard/Strict
  choice. To segment Android by ETP mode, JOIN
  `preferences.enhanced_tracking_protection` by `client_id` — do not use the
  captcha ping's privacy prefs. TIME-SENSITIVE: this reflects pre-fix builds.
  Bug 2054072 (D311582) makes Fenix persist the ETP-mode
  fingerprinting-protection choice at engine creation; once it rides out, true
  Strict Android clients will begin reporting `fpp=true`, so the
  Standard/Strict indistinguishability above (and the 99.4% figure) is specific
  to builds without that fix and will drift after it ships.

When segmenting by OS/platform, **re-derive each platform's modal composite** (the
most common key) rather than reusing another platform's predicates, and apply the
> 10k rule within the platform.

### Cohorts by engagement (pages-visited tier)
Threshold each **client-day** by the pages that client loaded **that day** — e.g.
**all / >= 20 / >= 200 pages/day** (use `pages_visited` for non-PBM cohorts,
`pages_visited_pbm` for PBM). Thresholding per client-day rather than on a
whole-window total lets a client fall in a higher tier on a busy day and a lower
one on a quiet day, so each (tier, day) draws its own client set. Notes:

- Page volume and challenge loads concentrate in heavy users, while explicit
  completions skew toward light users — so `Interacted` is very sensitive to the
  tier while **pass rate is largely tier-insensitive**. Always state the tier
  with any rate you quote.
- The higher tiers thin the PBM cohort far more than the normal-mode cohort (most
  clients barely browse in PBM), so a PBM "all" tier is dominated by near-inactive
  client-days.

### Weekdays vs. weekends / holidays
Weekend and holiday traffic differs materially from weekday traffic. **Default to
weekdays only and exclude holidays**; include weekends/holidays only when the
question is specifically about them.

- Weekday filter (BigQuery `DAYOFWEEK`: 1=Sun .. 7=Sat):
  `EXTRACT(DAYOFWEEK FROM DATE(submission_timestamp)) BETWEEN 2 AND 6`.
- Maintain an explicit holiday exclusion list for the market(s) you care about
  (US holidays are the usual default for Firefox analysis); extend it as needed.
- **Segment by day** and watch for anomalies. If a day is out of line with its
  neighbors, first check whether it is a holiday (exclude + add to the list); if
  not, apply the single-client spike rule below before treating it as real.
- **Firefox release days are another common source of spikes** (update-driven
  churn in the reporting population). They typically fall on weekdays, so the
  weekday filter does not remove them — cross-check anomalous days against the
  Firefox release calendar before treating a spike as organic.

### Excluding anomalous users
Three complementary layers:

1. **Automation filter.** Exclude obvious automation — at minimum
   `NOT is_bot_generated` (BrowserStack) when using the derived
   `*.captcha_detection` views.
2. **Invalid-ratio pings.** Some per-ping counter combinations are structurally
   impossible; a ping that violates one is corrupt / non-organic and should be
   dropped. Evaluate **per ping**, not per client over the window — a whole-window
   client sum hides one bad ping behind the client's good volume. Use a gross-only
   tolerance (e.g. `LHS > 2*RHS + 10`) so ordinary cross-ping straddles (a load in
   one ping, its outcome in the next) survive. See the invalid ratios below.
3. **Unusual load spikes.** On a day whose captcha-load volume is out of line with
   its neighbors (>= ~3 sigma), rank clients by their load volume and exclude any
   single client that alone is more than ~25% of that day's cohort total.
   Converging rule — removing a client re-shapes the day's mean/sigma, so iterate
   until nothing new fires. (As of 2026-07-13, applying this rule to the 90-day
   release population excluded 18 clients, converging over 3 rounds.)

#### Invalid ratios

Structural invariants — a loaded handler yields at most one terminal outcome, and
funnel stages are ordered. Evaluate per ping with the gross tolerance from layer 2
(`LHS > 2*RHS + 10`, and the `_pbm` equivalents) and drop the offending ping:

- **Cloudflare Turnstile** — `cc + cf <= oc` (the outcome observer disconnects
  after the first `#success`/`#fail` div, so at most one outcome per load).
- **reCAPTCHA v2** — `ac + ps <= oc`; `pc <= ps`.
- **hCaptcha** — `ac + ps <= oc`; `pc <= ps`.
- **Datadome** — `ps + bl <= oc`; `pc <= ps`. `pc_pbm <= ps_pbm` holds
  throughout, but the `_pbm` form of `ps + bl <= oc` is only evaluable on
  Firefox 154+ submissions, where `datadome_oc_pbm` exists (bug 2054037). On
  older rows it is NULL: skip the rule there rather than coalescing the load
  count to 0, which would flag every PBM ping carrying a Datadome outcome as
  invalid.
- **ArkoseLabs** — `pc + pf <= oc`.

**Caveat on the reCAPTCHA / hCaptcha `ac + ps <= oc` rule:** these vendors' outcome
counters accumulate across pings, and reCAPTCHA `ps` **over-counts** by firing on
element existence (bug 2054272; up to 76,156 in a single ping). So `ac + ps > oc`
predominantly flags that metric bug rather than corrupt data, and is by far the
largest contributor to the drop. Applying it removes those inflated-`ps` pings;
either way, treat reCAPTCHA `ps`-based ratios as inflated until 2054272 lands.

(As of 2026-07-13, applying all of the above to the 90-day release population
dropped ~216.5k pings across ~165.8k clients — ~0.1% of pings and ~0.4% of
reCAPTCHA clients; the reCAPTCHA `ac + ps > oc` rule alone was ~97% of that.)

### Querying (BigQuery)
Data lands in BigQuery as one dedup'd per-app view. Analysis over the whole
release population unions the two apps that carry the ping:
`mozdata.firefox_desktop.captcha_detection` and `mozdata.fenix.captcha_detection`
(Android) — views over the respective `*_stable.captcha_detection_v1` tables.
Client IDs are per-app namespaces: stack rows with `UNION ALL`; do NOT join across
apps by `client_id` (distinct-client counts still sum, since a client is in one
app). Metric columns are nested, e.g.
`metrics.counter.captcha_detection_cloudflare_turnstile_oc`,
`metrics.boolean.captcha_detection_privacy_resistfingerprinting`,
`metrics.string.captcha_detection_network_cookie_cookiebehavior`.

Always filter on `submission_timestamp` (the partition column) with an explicit
range; a `DATE()`-wrapped or OR-buried predicate is not accepted for partition
elimination. Then apply channel, the automation/invalid-client exclusions, and
the weekday/holiday filter as appropriate.
