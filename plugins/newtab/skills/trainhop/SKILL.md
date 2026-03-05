---
name: trainhop
description: Runs the New Tab train-hop release workflow for all automated steps: metabug, locales, metrics, Nimbus recipe, QA ticket, Confluence page, and version bump. Use when asked to "run the train-hop", "start a train-hop", or "do a train-hop". Do NOT use for individual steps like bumping the version or updating locales alone — those have their own skills.
argument-hint: "[bug-number] (optional)"
disable-model-invocation: true
---

# Train-hop: Full Workflow

## Before Starting

**Step 1: Ask the user which phase to run** (present as a numbered list):

> Which steps would you like to run?
>
> **1. Full workflow** — all automated steps from start to finish
> **2. Prep only** — steps 1–3: create metabug, update locales, update metrics (run before the XPI is cut)
> **3. Post-XPI** — steps 4–6: Nimbus recipe, QA ticket + Confluence page, version bump
> **4. Custom** — specify which numbered steps to include

Wait for the user's answer before continuing.

**Step 2: Collect inputs** — ask for the following based on the selected phase:

- If the phase includes step 4 (Nimbus recipe): **Ship task URL** from ShipIt
- If the phase includes step 5 (QA ticket + Confluence page):
  - **XPI cut date** (e.g. `2026-01-19`)
  - **QA handoff date** (e.g. `2026-01-20`)
  - **Release date** (e.g. `2026-01-22`)
  - **Release Management contact** (check https://whattrainisitnow.com for the release owner)
  - **QA contact** (QA engineer assigned to this train-hop)

**Step 3: Present the plan** — list the steps that will be executed and wait for confirmation before proceeding.

## Pre-conditions

Before running any steps, verify:

- Working tree is clean: `git status` shows no uncommitted changes
- On `main` branch and up to date: `git pull`
- Bugzilla API key is ready (see `references/credentials.md` if needed)
- Atlassian email and API token are ready (see `references/credentials.md` if needed)

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

### 5. File QA ticket and create Confluence page

Follow `references/file-qa-ticket.md`. Note the returned Jira ticket key.

Then follow `references/create-confluence-page.md`, passing:
- The meta bug number from step 1
- The QA ticket key from above
- The dates and contacts collected in the Inputs section

### 6. Bump minor version

Follow `references/bump-version.md`, passing the meta bug number from step 1.

## Troubleshooting

**A reference file is missing**
The skill may need to be reinstalled: `claude plugin install newtab`.

**Step fails partway through**
Report which step failed and its error output. Do not continue without explicit user instruction.
