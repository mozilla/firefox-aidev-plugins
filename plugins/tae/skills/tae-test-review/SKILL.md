---
name: tae-test-review
description: >-
  Review and authoring guidance for new/changed tests in the Fenix TAE
  efficiency framework
  (mobile/android/fenix/app/src/androidTest/java/org/mozilla/fenix/ui/efficiency).
  Use when reviewing a diff, PR, or Phabricator revision that adds or modifies
  files under that path — page objects, selectors, navigation edges, or test
  files. Also use when authoring a new test and self-checking before submission,
  when asked to check a test against TAE conventions, classify a test
  (presence/interaction/behavior), or judge whether a helper belongs in a page
  object vs. BasePage. Applies the framework's principles and anti-patterns as a
  review rubric with severity tiers.
---

# Contributing to the TAE Test Framework

## How to use this document

This one document serves two audiences:

- **Test authors — before you submit.** Read "Principles", "The three test
  types", and "Anti-patterns", then self-check your test against the "Before you
  write" checklist and the severity tiers in "Conducting a review". If any of
  your findings would be *blocking* for a reviewer, fix them first. For temporary
  1:1 smoke conversions, run each finding through the cost-of-fix gate in
  "Migration-era triage": fix the trivial ones yourself now, and flag the rest as
  known gaps so review is one pass, not a loop.
- **Reviewers — during code review.** Work from "Conducting a review". It routes
  you to the relevant principles and anti-patterns and gives severity tiers so
  your feedback tells the author what blocks merge.

Both audiences share the same rules; the only difference is who applies them and
when.

## Conducting a review

This section is for the reviewer (and for the author doing a pre-submission
self-check). The rest of the document defines what "good" looks like; this
defines how to apply it to a diff.

### Scope first

Identify what the diff touches, because different files get different scrutiny:

- **Test file** (`tests/*.kt`) — apply test-type classification, three-phase
  structure, and the one-assertion rule (with the Behavior exception below).
- **Page object** (`pageObjects/*.kt`) — check page-boundary discipline,
  whether new methods earn a `[STEP]`, and that navigation edges are registered
  in `init {}`.
- **Selectors** (`selectors/*Selectors.kt`) — check anchor stability, group
  assignment, and that nothing is defined inline in a test.
- **BasePage / helpers** — highest bar. A new primitive on BasePage is a
  blocking discussion, not a rubber stamp.

### Severity tiers

Label each finding so the author knows what blocks merge.

**Blocking** — merge only after this is fixed:
- Assertions interleaved with navigation in a Presence or Interaction test
  (see the Behavior exception below before flagging).
- `Thread.sleep()` or a hand-rolled poll/wait loop.
- Inline selector defined in a test file.
- New method added to `BasePage` without a demonstrated missing *category*.
- Page object method crossing page boundaries.
- `@After` used for state that must be clean for the next test to be valid.
- Hard-coded click sequence to reach a page instead of a `navigateToPage()`
  edge.

**Should-fix** — fix unless there's a stated reason:
- Test can't be classified as one of the three types, or does too much to be one.
- Setup done through the UI when a constructor flag or pre-seeded data exists.
- `mozVerifyElementsByGroup` used for runtime/dynamic data.
- Popup/dialog handling added inside a test instead of in a primitive/config.
- A wrapper method whose name adds no clarity over `primitive + selector`.

**Nit** — note it, don't block:
- Group name could be more meaningful.
- A method that could be reused but is currently test-local.
- Ordering/naming that reads slightly off-spec.

### Migration-era triage (temporary 1:1 conversions)

Most tests under review right now are 1:1 conversions of legacy smoke tests. They
are **temporary** — they exist until the factories generate the suite in CI — so
the goal is to get correct coverage landed with minimal round-trips, not to make
every conversion structurally perfect. The expensive thing is the feedback
*loop*, not the feedback. Recalibrate accordingly.

**Correctness is not a compromise variable.** Everything below relaxes structure,
placement, and primitive design. None of it relaxes whether the test actually
verifies its stated behavior. A green test that doesn't test the thing is
*negative* value during a migration: it reads as coverage while hiding a gap, and
if these hand-conversions seed factory templates, the wrong assertion
propagates. So correctness findings stay land-blocking no matter how the gate
below scores them.

**Cost-of-fix gate.** For every non-correctness finding, before requesting the
change, ask:

1. Does requesting it require more than ~1 day and another review round-trip?
2. Is the "better" way moderate+ complexity?
3. Is the preferred fix ambiguous because we have no existing example of it?
4. Does the fix require getting into the guts of BasePage primitives?
5. Is the root cause a missing harness/framework feature that should already exist?

If all five are "no", it's a **fix-now** item — trivial, has precedent, no guts —
and the author should just make it. If any is "yes", it's a **defer** item.

**Three buckets** (use these instead of raw blocking/should-fix/nit for
conversion patches):

- **Land-blocking** — correctness only. The test must verify its premise.
- **Fix-now** — trivial structural fixes that pass the gate (all five "no"):
  page-boundary swaps (`on.mainMenu` -> `on.downloads`), single-navigation
  assertion blocks, missing `all`-list registration, missing TestRail link.
- **Defer** — anything that trips the gate: BasePage primitive surgery,
  no-precedent design calls, or work blocked on missing harness support. Let it
  land; file the item into the cleanup backlog (see guardrails).

**Navigation and page-boundary findings are relax-by-default.** Do not block a
conversion solely because it chains across pages or over-navigates — *unless* the
fix is trivial-with-precedent (then it's fix-now). A test written awkwardly
because the harness lacks a clean step is a signal of a **missing feature**, not
an author error; record it as a gap rather than forcing the author to build the
primitive.

**Guardrails so "relaxed" doesn't become invisible debt:**

- **Track every defer.** A deferral that lives only in a review comment
  evaporates when cleanup starts. Emit defer items into the actual cleanup
  backlog (meta-bug / tag) so "temporary and incomplete" stays visible and
  temporary.
- **Watch what templates.** A one-off quirk in a throwaway test is fine; the same
  quirk in a pattern the factories will generalize from is not. That is the one
  structural class worth pushing on even when the fix is mildly non-trivial.
- **Batch, don't iterate.** Deliver one consolidated pass ("N trivial fixes, M
  deferred to cleanup") rather than a multi-round loop.

### Triage checklist (per changed test)

1. Classify it: Presence, Interaction, or Behavior. If you can't, that's a
   should-fix — the author doesn't have a clear subject.
2. Strip the navigation mentally. Does the remaining body read as one coherent
   spec? If it reads as several, check the Behavior exception, then decide split
   vs. keep.
3. Find the single assertion (or, for Behavior, the ordered checkpoints) that
   states why the test exists. If it's buried or absent, flag it.
4. Trace setup: could any of it move to a constructor flag, intent extra, or
   pre-seeded data? Every UI setup step is a should-fix candidate.
5. Check every selector used: does it exist in the selectors file with a
   meaningful group? Any inline selector is blocking.
6. Check every new page-object method: does it earn a `[STEP]`, and does it stay
   on the page it operates on?
7. Check navigation: is every hop a registered edge?

### The Behavior-test exception (read before flagging "interleaved assertions")

The "one test, one assertion" rule applies fully to **Presence** and
**Interaction** tests. **Behavior** tests legitimately span surfaces and may
contain *sequential checkpoints* — a verify after each state transition that a
later step depends on.

Distinguish a legitimate checkpoint from two tests glued together:

- **Legitimate checkpoint** — the verified state is a *precondition for the next
  step*, and removing it would make a later failure impossible to localize
  (e.g. verify a bookmark exists before opening its menu to edit it).
- **Glued-together tests** — the assertion blocks are independent; each could
  stand alone with its own setup, and neither depends on the other's state.
  Split these.

If in doubt, ask: "does the second assertion require the first action to have
happened?" Yes → checkpoint, allowed. No → split, blocking.

### Worked example

**Rejected** — inline selector, UI setup, and two unrelated assertions glued
together across navigation:

    @Test
    fun bookmarksTest() {
        // UI setup that a constructor flag / pre-seed could do
        on.browserPage.navigateToPage(url)
        on.browserPage.openMainMenu().mozClick(MainMenuSelectors.BOOKMARK_THIS)

        on.bookmarks.navigateToPage()
            .mozVerify(Selector(COMPOSE_BY_TEXT, "My Page", groups = listOf())) // inline selector
            .mozClick(BookmarksSelectors.THREE_DOT_MENU)                        // crosses into an action
        on.bookmarks.mozVerify(BookmarksSelectors.EDIT_BUTTON)                  // assertion #1: menu opens

        on.home.navigateToPage()                                               // unrelated surface
            .mozVerifyElementsByGroup("jumpBackIn")                            // assertion #2: independent
    }

Review comments:
- **Blocking**: inline selector — move to `BookmarksSelectors` with a group.
- **Blocking**: two independent assertions (bookmark menu, then Jump Back In)
  glued by navigation — the second doesn't depend on the first. Split into two
  tests.
- **Should-fix**: the bookmark is created through the UI — pre-seed it with
  `createBookmarkItem(...)` so this test starts on the surface it's verifying.

**Accepted** — one Presence test, setup pre-seeded, single assertion. Note the
assertion uses `mozVerify` with a parameterized selector (`BOOKMARK_ITEM(title)`)
rather than a group, because `title` is runtime data — this is correct, not a
missing group:

    @Test
    fun bookmarksListShowsSavedItem() {
        // SETUP
        createBookmarkItem(url, title, null)

        // STEPS
        on.bookmarks.navigateToPage()

        // ASSERT
        on.bookmarks.mozVerify(BookmarksSelectors.BOOKMARK_ITEM(title))
    }

## Principles

### Tests declare what, not how

A test should read as a specification of behavior. Navigation mechanics, element resolution, retries, and waits belong in the framework. If someone reads your test and can't tell what feature it validates within 10 seconds, rewrite it.

### One test, one assertion (with a Behavior-test exception)

For **Presence** and **Interaction** tests: if you have assertion blocks
separated by navigation or interaction steps, you have written multiple tests
glued together. Split them. Use `mozVerifyElementsByGroup` to assert multiple
related elements as one logical check when they belong to the same verification.

For **Behavior** tests: because they intentionally cross surfaces, a verify may
appear after each state transition as a *sequential checkpoint* — but only when
that verified state is a precondition for the next step and removing it would
make a later failure impossible to localize. Independent assertion blocks that
don't depend on each other's state are still two tests; split them.

The distinguishing question: *does the next action require the previous
assertion's state to have happened?* Yes → legitimate checkpoint. No → split.

(See "Conducting a review > The Behavior-test exception" for how this is applied
in review.)

### Three-phase structure

Every test follows this pattern:

```kotlin
// SETUP: what preconditions does this test need?
// Prefer BaseTest constructor flags, pre-seeded data, or pre-runner state.
// Reserve in-test setup for state that genuinely requires UI interaction.
createBookmarkItem(url, title, null)

// STEPS: navigation and page object interactions to reach the point of interest.
on.bookmarks.navigateToPage()
    .openItemMenu(title)
    .mozClick(BookmarksSelectors.SHARE_BUTTON)

// ASSERT: a single assertion block capturing the spirit of the test.
// This is WHY the test exists and WHAT artifact is being verified.
on.shareOverlay.mozVerifyElementsByGroup("shareTabLayout")
```

Push setup as early as possible. If state can be configured via feature flags in the `BaseTest` constructor, do that. If it can be set before the runner initializes (intent extras, shared prefs), do that.

## The three test types

Before writing a test, identify which type it is. Each has a repeatable model:

**Presence** - Navigate to a surface, verify elements render. No state changes. Answers: *"Does this page show what it should?"*
```kotlin
on.home.navigateToPage()
    .mozVerifyElementsByGroup("requiredForPage")
```

**Interaction** - Navigate + perform an action + verify the immediate result. Modifies state on one surface. Answers: *"Does this control do what it should?"*
```kotlin
on.home.navigateToPage()
    .mozClick(HomeSelectors.PRIVATE_BROWSING_BUTTON)
on.home.mozVerifyElementsByGroup("privateBrowsing")
```

**Behavior** - One or more state changes across one or more pages. Answers: *"Does this feature work end-to-end?"* These compose presence and interaction primitives.
```kotlin
on.browserPage.navigateToPage(url)
on.home.navigateToPage()
    .mozVerifyElementsByGroup("jumpBackIn")
```

If you can't classify your test, you don't yet have a clear enough picture of what you're testing.

## Reuse over specificity

### Write for reuse by default

Before adding a function, ask: "Would another test for a different feature need this?" If yes, it belongs in a page object or shared step. If no, reconsider whether you need a new function at all.

### Page objects are shared vocabulary

If you add a method to a page object, it should be useful to any test touching that page. If only your test calls it, it doesn't belong there.

### Test steps belong on the page they operate on

A page object method should only interact with the UI surface it represents. If a method on `BrowserPage` clicks through MainMenu and Collections selectors, it's crossing page boundaries -- put it on the page where the action starts, or split it across the relevant page objects. Similarly, don't chain primitives on one page object while interacting with another page's UI just because the return type allows it.

### Selectors are shared vocabulary too

Define selectors once in the appropriate `selectors/*Selectors.kt` file. Assign meaningful groups. Don't create one-off selectors inline in tests.

## Primitives and test steps

### Use the existing primitives

`mozClick`, `mozSwipeTo`, `mozVerify`, `mozVerifyElementsByGroup`, `mozEnterText`, `mozPressEnter` -- these are your building blocks. Compose tests from them.

> Verified against `helpers/BasePage.kt` on 2026-07-06. This is a point-in-time
> snapshot — new primitives are added over time, so treat the current BasePage
> source as authoritative if it differs. `mozVerifyElement` and `mozClear` are
> **internal** to BasePage and are intentionally omitted; do not call them from
> tests.

### Interaction primitives

| Primitive | Purpose |
|-----------|---------|
| `mozClick(selector)` | Click an element |
| `mozLongClick(selector)` | Long-click an element |
| `mozClickIfPresent(selector)` | Click only if the element is present (no failure if absent) |
| `mozClickFirstWithParentText(selector, parentText)` | Click the first match under a parent with given text |
| `mozEnterText(text, selector)` | Enter text into a field |
| `mozClearAndEnterText(text, selector)` | Clear then enter text |
| `mozPressEnter(selector)` | Press the IME enter key on the field |
| `mozSwipeTo(selector)` | Swipe until an element is visible |
| `mozSwipeElement(selector, direction)` | Swipe a specific element in a direction |
| `mozPressBackUntilGone(selector)` | Press back repeatedly until an element is gone |
| `mozOpenNotificationsTray()` | Open the system notifications tray |
| `navigateToPage()` | Navigate via the navigation graph |

### Verification primitives

| Primitive | Purpose |
|-----------|---------|
| `mozVerify(selector)` | Verify a single element is displayed |
| `mozVerifyElementsByGroup(group)` | Verify all selectors in a group (compile-time selectors only) |
| `mozVerifyElementAbsent(selector)` | Verify an element is not displayed |
| `mozWaitUntilAbsent(selector)` | Wait until an element is no longer present |
| `mozVerifyAnyContainsText(selector, text)` | Verify any match contains the given text |
| `mozVerifyAnyHasChildWithText(selector, text)` | Verify any match has a child with the given text |
| `mozVerifyNoneContainText(selector, text)` | Verify no match contains the given text |
| `mozVerifyElementIsSelected` / `mozVerifyElementNotSelected` | Verify selected state |
| `mozVerifyElementIsChecked` / `mozVerifyElementIsNotChecked` | Verify checked state |
| `mozVerifyElementIsEnabled` / `mozVerifyElementIsNotEnabled` | Verify enabled state |
| `mozVerifyElementHasCheckedSiblingByResName` | Verify a sibling (by res name) is checked |
| `mozVerifyElementHasSiblingWithText` | Verify a sibling has given text |
| `verifySnackbarText(text)` | Verify a snackbar shows the given text |
| `waitForSnackbarToBeDismissed()` | Wait for the snackbar to dismiss |

The state-verification family (`...IsSelected`, `...IsChecked`, `...IsEnabled`,
sibling checks) is easy to overlook — reach for these before writing a custom
check when asserting toggle/checkbox/selection state. Their exact parameter
lists vary; check the current `helpers/BasePage.kt` signatures before use.

### Do not extend BasePage

Don't add new primitives to `BasePage.kt` unless you've identified a genuinely missing *category* of interaction that multiple pages need. The bar for adding to BasePage is high.

### Don't create framework-level abstractions

No `clickAndWaitForBookmarks()` -- that's `mozClick` + `navigateToPage`. No `interactAndWait()` -- that's a primitive trying to be a framework. These belong in BasePage if anywhere.

### Custom commands over custom waits

If you're tempted to write a new wait/polling mechanism, you probably need a better selector (one that keys off the right element state) rather than new timing logic.

### When to wrap primitives into page object test steps

Page object methods are test steps. The structured log hierarchy is `[STEP]` > `[CMD]` > `[LOC]` > `[SEL]`, and test steps should read like steps in a TestRail test case. The question isn't "how many primitives does it wrap?" but "does wrapping improve logging and root cause analysis?"

**Wrap when:**
- The method name maps to a recognizable user action that would appear as a TestRail step (e.g., `openMainMenu`, `openItemMenu`, `saveEditBookmark`)
- A `[STEP]`-level failure in the log would immediately tell you what user action broke -- without reading the underlying `[CMD]`s -- with close to zero processing effort
- The grouping represents a logical user action, even if it's one primitive today

**Don't wrap when:**
- The wrapper name doesn't add clarity beyond primitive + selector (e.g., `verifyBookmarkTitle(title)` vs `mozVerify(BookmarksSelectors.BOOKMARK_ITEM(title))` -- these read identically)
- You're wrapping just to avoid typing the selector object name

This matters because the structured logging is designed as a bidirectional bridge to TestRail: well-named test steps, commands, locators, and selectors mean TestRail cases can generate tests via factories, and test logging can maintain TestRail cases. AI can also generate test scaffolding from selectors, navigation nodes, and page object test steps. This flow only works when each layer is meaningful and reads like a test case.

## Selectors and element strategy

### Choose stable anchors

Selectors should represent stable, semantic anchors: test tags, resource IDs, accessibility labels. Avoid selectors tied to layout position, localized text, or internal implementation details.

### Use groups to express intent

- `"requiredForPage"` -- elements that prove the page loaded
- `"jumpBackIn"`, `"topSitesCompose"` -- elements that constitute a feature area
- `"homeScreen"` -- elements belonging to a broader surface

Groups turn element lists into meaningful assertions.

### Groups are for static elements; use multiple `mozVerify` calls for dynamic data

`mozVerifyElementsByGroup` works with selectors defined at compile time in the selectors file. When values come from test data at runtime (e.g., verifying that specific page titles appear in a collection), use individual `mozVerify` calls with parameterized selectors. Multiple `mozVerify` calls in the same assertion block on the same page is fine -- it's not the same anti-pattern as splitting assertions across navigation.

### Prefer existing selector strategies

The 20+ strategies in `SelectorStrategy` cover Compose, Espresso, and UIAutomator. If none works, the UI itself may need a test hook (a test tag or content description) rather than a more complex selector.

## Navigation

### Use the registry

All navigation goes through `navigateToPage()`. Hard-coded click sequences to reach a page mean the registry is missing an edge -- add the edge, don't work around it.

### Register edges in page object init blocks

This keeps the graph definition co-located with the page that owns the relationship:

```kotlin
class HomePage(...) : BasePage(composeRule) {
    override val pageName = "HomePage"

    init {
        NavigationRegistry.register(
            from = "AppEntry",
            to = pageName,
            steps = listOf(),
        )
        NavigationRegistry.register(
            from = pageName,
            to = "MainMenuPage",
            steps = listOf(NavigationStep.Click(HomeSelectors.MAIN_MENU_BUTTON)),
        )
    }
}
```

### Navigation is not a test step

Getting to the page is infrastructure. Your test starts once you're *on* the page. If navigation dominates your test body, your test is too far from its subject.

## Anti-patterns

These should be flagged in code review:

| Anti-pattern | Why it's wrong | What to do instead |
|---|---|---|
| Assertions interleaved with navigation | Multiple tests combined into one | Split into separate tests |
| New methods on BasePage | Framework bloat | Use existing primitives |
| Inline selectors in test files | Not reusable | Add to selectors file with groups |
| `Thread.sleep()` or custom polling | Brittle, flaky | Use `requiredForPage` or existing waits |
| Wrappers that don't add log clarity | Name doesn't aid root cause analysis | Use the primitive + selector directly |
| UI setup when config is available | Slower, flakier | Use constructor flags or pre-seeded data |
| Journey tests without foundational coverage | Premature | Write presence/interaction tests first |
| Framework-level abstractions in page objects | Belongs in BasePage if anywhere | Keep page object methods as test steps, not new primitives |
| Page object methods crossing page boundaries | Breaks page object model | Put methods on the page they operate on, or use separate `on.<page>` calls |
| Using `mozVerifyElementsByGroup` for dynamic data | Groups are compile-time; dynamic values won't match | Use individual `mozVerify` calls with parameterized selectors |
| Using `@After` for critical state cleanup | If the runner crashes, `@After` is not called -- leaves dirty state that can break subsequent tests or worse, cause false passes from carried-over state | Push cleanup to pre-test setup, constructor flags, or runner-level mechanisms that run regardless of crash |
| Handling unexpected popups in test assertions | System alerts, permission dialogs, and conditional modals break tests that aren't meant to verify them | Let custom commands handle view-blocking elements via fallback conditional checks -- this keeps the fix in one place (the primitive) rather than scattered across tests |

## Handling unexpected popups and system dialogs

Tests that aren't specifically verifying a popup, alert, or modal should not fail because one appeared unexpectedly. The framework's custom commands are designed to handle this: locators inside primitives can include fallback checks for view-blocking elements (system alerts, client popups, app modals) in priority order.

Don't add popup handling logic to individual tests. If a system dialog or conditional modal is blocking your test:
- If it appears reliably, suppress it via configuration (e.g., `isPageLoadTranslationsPromptEnabled = false` in the BaseTest constructor)
- If it appears sometimes, the custom command that encounters it should handle the dismissal -- one fix in one place
- If it requires state detection (e.g., permission state determines whether a dialog appears), use that state to drive conditional checks within the primitive, not the test

The goal is stability first, speed second. Adding conditional checks for view-blocking elements in custom commands is acceptable overhead -- it's cheaper than flaky tests.

## Before you write: checklist

1. What type of test is this? (Presence / Interaction / Behavior)
2. What is the single assertion that captures why this test exists?
3. Can the setup be pushed to constructor flags or pre-runner state?
4. Do the selectors I need already exist? Are they in the right groups?
5. Do the page object methods (test steps) I need already exist?
6. For any new test step: does the method name create a meaningful `[STEP]` in the log? Would a failure at that level immediately tell you what broke?
7. If I removed all the navigation, does the test body still make sense as a spec?

## Adding a new page

1. Create selectors in `selectors/NewPageSelectors.kt` with groups (at minimum `"requiredForPage"`)
2. Create page object in `pageObjects/NewPage.kt` extending `BasePage`
3. Register navigation edges in `init {}`
4. Implement `mozGetSelectorsByGroup()`
5. Add page instance to `helpers/PageContext.kt` for use in tests
