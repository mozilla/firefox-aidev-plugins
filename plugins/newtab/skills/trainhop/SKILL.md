---
name: trainhop
description: Runs the complete New Tab train-hop workflow from start to finish. Use when asked to "run the train-hop", "start a train-hop", "do a train-hop release", or "perform a train-hop". Optionally pass an existing Bugzilla bug number. Do NOT use for individual steps of the train-hop process.
argument-hint: "[bug-number] (optional)"
disable-model-invocation: true
---

# Train-hop: Full Workflow

Orchestrates the complete New Tab train-hop release process by invoking each child skill in sequence. Stop and report to the user if any step fails.

## Important

Do not skip any steps. Complete each step fully before moving to the next. If a step is marked "not yet automated", pause and instruct the user to complete it manually before continuing.

## Steps

### 1. Update locales

Invoke `/trainhop-update-locales`.

### 2. Update metrics

Invoke `/trainhop-update-metrics`.

### 3. Build and sign the XPI via ShipIt

_Not yet automated._ Instruct the user to:
- Sign into the corporate VPN
- Visit https://shipit.mozilla-releng.net/newxpi, select "newtab", enter the GitHub SHA, and create the release
- Coordinate with a second HNT engineer for the two-engineer sign-off
- Copy the Ship task URL once the build completes

Wait for the user to provide the Ship task URL before continuing.

### 5. Generate the Nimbus recipe

Invoke `/trainhop-generate-recipe` passing the Ship task URL provided in step 4.

### 6. Create Stage Experimenter rollout for QA

_Not yet automated._ Instruct the user to:
- Sign into the staging version of Experimenter
- Clone the existing QA rollout template
- Set the newtabTrainhopAddon feature value to the recipe from step 5
- Set min/max Firefox version numbers
- Request rollout approval for QA

Wait for the user to confirm the stage rollout is live before continuing.

### 7. File QA ticket

Invoke `/trainhop-file-qa-ticket` passing $ARGUMENTS (the bug number, if provided).

### 8. Create Production Experimenter rollouts

_Not yet automated._ Instruct the user to create three rollouts on the production Experimenter instance:
- **Prior version rollout**: lock to minimum version, exclude from new rollout
- **Release rollout**: new version, start at 25% (or 100% if a prior rollout exists)
- **Beta rollout**: new version, 100%

Remind the user: do not request approval yet — wait for QA sign-off.

### 9. Bump minor version

Invoke `/trainhop-bump-version` passing $ARGUMENTS (the bug number, if provided).

### 10. Wait for QA sign-off

Pause and prompt the user to confirm QA has returned a green report before continuing.

### 11. Ship to Release and Beta

_Not yet automated._ Instruct the user to:
- Alert `#system-addon-release-process` in Slack with the QA report and rollout link
- Request Release Management approval on the production Release rollout
- Once approved, throttle/end prior rollouts as needed and ramp to 100% over the following days
- Approve the Beta rollout immediately at 100%

### 12. Find backward-compat shims to clean up

Invoke `/trainhop-find-compat-shims`.

## Troubleshooting

**A child skill is not installed**
Inform the user which skill is missing and that it can be installed via `claude plugin install newtab`.

**Step fails partway through**
Report which step failed and its error output. Do not attempt to continue past a failed step without explicit user instruction.
