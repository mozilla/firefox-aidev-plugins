---
name: trainhop
description: Runs the New Tab train-hop release workflow for all automated steps: metabug, locales, metrics, Nimbus recipe, Confluence page, QA ticket, and version bump. Use when asked to "run the train-hop", "start a train-hop", or "do a train-hop". Do NOT use for individual steps like bumping the version or updating locales alone — those have their own skills.
argument-hint: "[bug-number] (optional)"
disable-model-invocation: true
---

# Train-hop: Full Workflow

## Before Starting

**Step 1: Ask the user which phase to run** (present as a numbered list):

> Which steps would you like to run?
>
> **1. Full workflow** — all automated steps from start to finish
> **2. Prep only** — steps 1–3: filings (metabug + Confluence page + QA ticket), update locales, update metrics (run before the XPI is cut)
> **3. Post-XPI** — steps 4–6: Nimbus recipe, update Confluence page with real QA ticket reference, version bump
> **4. Custom** — specify which numbered steps to include

Wait for the user's answer before continuing.

**Step 2: Collect inputs** — ask for the following based on the selected phase:

- If the phase includes step 1 (Confluence page + QA ticket):
  - **XPI cut date** (e.g. `2026-05-13`)
  - **QA handoff date** (e.g. `2026-05-14`)
  - **QA sign-off date** (e.g. `2026-05-18`) — also used as the Jira ticket's due date
  - **Release date** (e.g. `2026-05-19`)
  - **Release Management contact** — name + Atlassian accountId (check https://whattrainisitnow.com for the release owner; resolve accountId via `mcp__atlassian__lookupJiraAccountId`)
  - **QA contact** — name + Atlassian accountId (default: Valentin Bandac, accountId `6310ac8255b0a9e29f1af16d`)
  - **Conductor** — name + Atlassian accountId (typically the person running this workflow)
- If the phase includes step 4 (Nimbus recipe): **Ship task URL** from ShipIt

**Step 3: Present the plan** — list the steps that will be executed and wait for confirmation before proceeding.

## Pre-conditions

Before running any steps, verify:

- Working tree is clean: `git status` shows no uncommitted changes
- On `main` branch and up to date: `git pull`
- Bugzilla API key is available (`BUGZILLA_API_KEY` env var or interactive prompt — see `references/credentials.md`)
- The **Atlassian MCP plugin** is installed and authenticated — used for both the Jira ticket and the Confluence page. Install from the official Anthropic marketplace with `/plugin install atlassian@claude-plugins-official` followed by `/reload-plugins`. The plugin runs an OAuth flow on first use; no API token to manage. See `references/credentials.md` for full setup, troubleshooting, and the legacy API-token fallback.

## Steps

Stop and report to the user if any step fails. Do not proceed past a failed step without explicit instruction.

### 1. File meta bug, Confluence page, and QA ticket

This is a three-substep flow. Do them in order:

#### 1a. Create the meta bug

Follow `references/create-metabug.md`. Note the returned bug number — pass it to all subsequent steps.

#### 1b. Create the Confluence page (with `QA-TBD` placeholder)

Follow `references/create-confluence-page.md`, passing:
- The meta bug number from step 1a (full URL form)
- A placeholder for the QA ticket (`QA-TBD`) — the page will be updated in step 5
- All four dates (XPI Cut, QA Handoff, QA Sign-off, Release) as Unix epoch milliseconds for ADF `date` nodes
- Rel Man, QA, and Conductor as ADF `mention` nodes (name + accountId)

Note the returned **page ID** and **page URL**.

#### 1c. File the QA ticket

Follow `references/file-qa-ticket.md`, passing:
- The meta bug URL from step 1a
- The Confluence page URL from step 1b
- The QA sign-off date (becomes the Jira ticket's due date)
- The QA contact's accountId (for `assignee_account_id`)
- The conductor's name (for `customfield_10138` Feature Owner)

Note the returned **QA ticket key** (e.g. `QA-5234`).

### 2. Update locales

Follow `references/update-locales.md`, passing the meta bug number from step 1a.

### 3. Update metrics

Follow `references/update-metrics.md`, passing the meta bug number from step 1a.

### 4. Generate the Nimbus recipe

```bash
./mach newtab trainhop-recipe <ship-task-url>
```

Use the Ship task URL collected in the Inputs section. Display the full output.

### 5. Update the Confluence page with the real QA ticket reference

Use `mcp__atlassian__updateConfluencePage` to replace the `QA-TBD` placeholder on the page from step 1b with a real link to the ticket key from step 1c. Pass `versionMessage: "Fill in QA ticket reference (QA-XXXX)"`.

### 6. Bump minor version

Follow `references/bump-version.md`, passing the meta bug number from step 1a.

## Troubleshooting

**A reference file is missing**
The skill may need to be reinstalled: `claude plugin install newtab`.

**Step fails partway through**
Report which step failed and its error output. Do not continue without explicit user instruction.

**MCP call denied by the auto-mode classifier**
Re-prompt the user — these calls (Jira ticket creation, Confluence page creation/update) are intentional and on the user's behalf.

**Atlassian MCP unavailable**
The `scripts/file_jira_ticket.py` and `scripts/create_confluence_page.py` Python scripts are kept as a legacy fallback. They require `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_NAME` env vars and emit the older plain-text Confluence template (no date macros, no `@mention`s, no QA Sign-off, no Conductor row).
