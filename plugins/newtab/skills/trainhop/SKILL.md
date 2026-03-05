---
name: trainhop
description: Runs the complete New Tab train-hop workflow from start to finish. Use when asked to "run the train-hop", "start a train-hop", "do a train-hop release", or "perform a train-hop". Optionally pass an existing Bugzilla bug number. Do NOT use for individual steps of the train-hop process.
argument-hint: "[bug-number] (optional)"
disable-model-invocation: true
---

# Train-hop: Full Workflow

Orchestrates the complete New Tab train-hop release process. Stop and report to the user if any step fails.

## Important

Do not skip any steps. Complete each step fully before moving to the next. If a step is marked "not yet automated", pause and instruct the user to complete it manually before continuing.

## Steps

### 0. Check for Bugzilla API key

Check for a `BUGZILLA_API_KEY` in the following order:

1. Check if the environment variable is already set: `echo $BUGZILLA_API_KEY`
2. If not set, check for a `.env` file in the root of the Firefox source tree and look for a `BUGZILLA_API_KEY=` entry

If a key is found, confirm it is set and continue.

If no key is found, stop and instruct the user:

> A Bugzilla API key is required to file bugs automatically during this workflow.
> To create one:
> 1. Go to https://bugzilla.mozilla.org and sign in
> 2. Click your name in the top-right → **Preferences** → **API Keys**
> 3. Enter a description (e.g. "train-hop automation") and click **Generate Key**
> 4. Copy the generated key and add it to your Firefox `.env` file:
>    ```
>    BUGZILLA_API_KEY=your-key-here
>    ```
>    Or export it in your shell profile (`~/.zshrc`):
>    ```
>    export BUGZILLA_API_KEY=your-key-here
>    ```

Wait for the user to confirm the key is set before continuing.

### 1. Create meta bug

Follow the instructions in `references/create-metabug.md`. Note the returned meta bug number — it will be used in all subsequent steps.

### 2. Update locales

Follow the instructions in `references/update-locales.md`, passing the meta bug number from step 1.

### 3. Update metrics

Follow the instructions in `references/update-metrics.md`, passing the meta bug number from step 1.

### 4. Build and sign the XPI via ShipIt

_Not yet automated._ Instruct the user to:
- Sign into the corporate VPN
- Visit https://shipit.mozilla-releng.net/newxpi, select "newtab", enter the GitHub SHA, and create the release
- Coordinate with a second HNT engineer for the two-engineer sign-off
- Copy the Ship task URL once the build completes

Wait for the user to provide the Ship task URL before continuing.

### 5. Generate the Nimbus recipe

Run:

```bash
./mach newtab trainhop-recipe <ship-task-url>
```

Display the full output to the user. They will need `addon_version` and `xpi_download_path` to complete step 6.

### 6. Create Stage Experimenter rollout for QA

_Not yet automated._ Instruct the user to:
- Sign into the staging version of Experimenter
- Clone the existing QA rollout template
- Set the newtabTrainhopAddon feature value to the recipe from step 5
- Set min/max Firefox version numbers
- Request rollout approval for QA

Wait for the user to confirm the stage rollout is live before continuing.

### 7. File QA ticket

_Not yet automated._ Instruct the user to file a QA ticket, linking to the meta bug from step 1.

### 8. Create Production Experimenter rollouts

_Not yet automated._ Instruct the user to create three rollouts on the production Experimenter instance:
- **Prior version rollout**: lock to minimum version, exclude from new rollout
- **Release rollout**: new version, start at 25% (or 100% if a prior rollout exists)
- **Beta rollout**: new version, 100%

Remind the user: do not request approval yet — wait for QA sign-off.

### 9. Bump minor version

Follow the instructions in `references/bump-version.md`, passing the meta bug number from step 1.

### 10. Wait for QA sign-off

Pause and prompt the user to confirm QA has returned a green report before continuing.

### 11. Ship to Release and Beta

_Not yet automated._ Instruct the user to:
- Alert `#system-addon-release-process` in Slack with the QA report and rollout link
- Request Release Management approval on the production Release rollout
- Once approved, throttle/end prior rollouts as needed and ramp to 100% over the following days
- Approve the Beta rollout immediately at 100%

### 12. Find backward-compat shims to clean up

_Not yet automated._ Instruct the user to search for backward-compatibility shims in the newtab codebase that can now be removed.

## Troubleshooting

**A reference file is missing**
Inform the user which file is missing and that the skill may need to be reinstalled via `claude plugin install newtab`.

**Step fails partway through**
Report which step failed and its error output. Do not attempt to continue past a failed step without explicit user instruction.
