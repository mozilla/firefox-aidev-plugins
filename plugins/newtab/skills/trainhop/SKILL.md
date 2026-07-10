---
name: trainhop
description: Runs the New Tab train-hop release workflow for all automated steps: metabug, locales, metrics, Nimbus recipe, Confluence page, and QA ticket. Use when asked to start a train-hop. Do NOT use for individual steps like updating locales alone — those have their own skills.
argument-hint: "[bug-number] (optional)"
disable-model-invocation: true
---

# Train-hop: Full Workflow

## Before Starting

**Step 1 — Pick the phase.** Ask (numbered list):

> Which steps would you like to run?
>
> **1. Full workflow** — all steps, start to finish
> **2. Prep only** — steps 1–3 (metabug, locales, metrics), run before the XPI is cut
> **3. Post-XPI** — steps 4–5 (Nimbus recipe, Confluence page + QA ticket)
> **4. Custom** — specify which step numbers to include

**Step 2 — Resolve, ask, confirm.** Resolve what you can automatically, ask the user only for the rest, then present the plan and wait for a single confirmation.

*Resolve automatically:*
- **`TARGET_VERSION`** — read the Nightly major from `browser/config/version.txt`; the release target is `Nightly − 2` (e.g. `154` → `152`). This labels the meta bug, per-step bugs, QA ticket, and Confluence title — **not** the Nightly version. Use it everywhere; don't re-derive it per step.
- **Conductor** — defaults to the signed-in user (`${MCP}atlassianUserInfo`).
- **QA contact** — defaults to Valentin Bandac (`6310ac8255b0a9e29f1af16d`).
- **accountIds** — resolve names → accountIds with `${MCP}lookupJiraAccountId`.

*Ask the user (only what the chosen phase needs):*
- **Target version** — confirm the computed `Nightly − 2` default, or take an override.
- If step 4 is included — **Ship task URL** (from ShipIt).
- If step 5 is included:
  - **Dates**: XPI cut, QA handoff, QA sign-off (= the Jira due date), and the staged **Release** dates — 50% and 100% (usually consecutive days).
  - **Rel Man** — name only (check https://whattrainisitnow.com/release/?version=release if unknown).
  - **Conductor & QA contact** — default to you (the signed-in user) and Valentin Bandac; confirm, or name someone else.

Then show the resolved target version and the exact steps to run, and wait for one confirmation before proceeding.

## Pre-conditions

Run these checks at the start — don't ask the user to verify them. If something is off, explain it in plain language and wait.

1. **In the Firefox checkout.** Confirm `browser/config/version.txt` exists in the working directory. If not, the workflow is running from the wrong place — ask the user to start it from their local Firefox source checkout (every step operates there).
2. **Clean tree on `main`.** Run `git status --porcelain` and `git rev-parse --abbrev-ref HEAD`. If there are uncommitted changes or the branch isn't `main`, stop and say so plainly (e.g. "there are unsaved changes in the Firefox repo" / "you're on branch X, not `main`") and ask how to proceed — do not run on a dirty tree. Once clean and on `main`, run `git pull` to get up to date.
3. **Bugzilla API key.** The key must be a non-empty `BUGZILLA_API_KEY` line in `~/.mozbuild/trainhop.env`. Check with:
   ```bash
   grep -qE '^BUGZILLA_API_KEY=.+' ~/.mozbuild/trainhop.env && echo ok
   ```
   If that prints `ok`, continue. If not (file missing or value empty), the key isn't set up: point the user to the setup doc — https://mozilla-hub.atlassian.net/wiki/x/QoA4qg — and **stop** until they've created the file in their own terminal, then re-check. **Never ask for the key in the chat, prompt for it, or write it yourself** — the key must never enter the Claude session. You only verify it's present.
4. **Atlassian MCP** (only needed for step 5). The Atlassian MCP plugin must be installed and authenticated: `/plugin install atlassian@claude-plugins-official` then `/reload-plugins` (OAuth on first use, no token). See `references/credentials.md` for setup and the `${MCP}` tool-prefix note.

## Steps

Stop and report to the user if any step fails. Do not proceed past a failed step without explicit instruction.

### 1. Create meta bug

Follow `references/create-metabug.md`. Note the returned bug number — pass it to all subsequent steps.

### 2. Update locales

Follow `references/update-locales.md`, passing the meta bug number from step 1.

### 3. Update metrics

Follow `references/update-metrics.md`, passing the meta bug number from step 1.

### 4. Generate the Nimbus recipe

```bash
./mach newtab trainhop-recipe <ship-task-url>
```

Use the Ship task URL collected in the Inputs section. Display the full output.

### 5. Create Confluence page and file QA ticket

This is a three-substep flow. Do them in order:

#### 5a. Create the Confluence page (with `QA-TBD` placeholder)

Follow `references/create-confluence-page.md`, passing:
- The meta bug number from step 1 (full URL form)
- A placeholder for the QA ticket (`QA-TBD`) — the page will be updated in step 5c
- The dates (XPI Cut, QA Handoff, QA Sign-off, Release 50%/100%) as `YYYY-MM-DD` for HTML `<time>` nodes
- Rel Man, QA, and Conductor as HTML `<span data-type="mention">` nodes (name + accountId)

Note the returned **page ID** and **page URL**.

#### 5b. File the QA ticket

Follow `references/file-qa-ticket.md`, passing:
- The meta bug URL from step 1
- The Confluence page URL from step 5a
- The QA sign-off date (becomes the Jira ticket's due date)
- The QA contact's accountId (for `assignee_account_id`)
- The conductor's name (for `customfield_10138` Feature Owner)

Note the returned **QA ticket key** (e.g. `QA-XXXX`).

#### 5c. Update the Confluence page with the real QA ticket reference

Use `${MCP}updateConfluencePage` to replace the `QA-TBD` placeholder with a real link to the ticket key from 5b. Pass `versionMessage: "Fill in QA ticket reference (QA-XXXX)"`.

## Troubleshooting

**A reference file is missing**
The skill may need to be reinstalled: `claude plugin install newtab`.

**Step fails partway through**
Report which step failed and its error output. Do not continue without explicit user instruction.

**MCP call denied by the auto-mode classifier**
Re-prompt the user — these calls (Jira ticket creation, Confluence page creation/update) are intentional and on the user's behalf.

**Atlassian MCP unavailable**
Create the Confluence page and QA ticket manually in the UI by cloning a recent one — see the "If the Atlassian MCP is unavailable" notes in `references/create-confluence-page.md` and `references/file-qa-ticket.md`.
