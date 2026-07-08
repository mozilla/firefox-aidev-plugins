---
name: trainhop-adv-target
description: End-to-end New Tab train-hop targeting for the Experimenter repo. From a single trainhop version string, files the GitHub targeting issue, branches, adds the NimbusTargetingConfig entry, lints, and stages a drafted commit. Use for "newtab trainhop targeting" requests.
---

# New Tab Train-hop Targeting

Run the whole recurring train-hop targeting task end-to-end. The **only** required input
is the trainhop version string; everything else is derived.

## Input

- **Version string**, format `major.minor.YYYYMMDD.buildid`, e.g. `153.4.20260610.40323`.
  If not given, ask for it.
- **Fx major** for the "includes users of" line — defaults to `151`; override only if told.

## Steps

### 1. Ask for the version

If the user didn't supply the trainhop version, ask for it. That is the only input needed.

### 2. Derive values

From `major.minor.YYYYMMDD.buildid`:

- Python var: `FX_<major>_<minor>_TRAINHOP` (drop `_<minor>` only if minor is `0`/first of
  that major — check what's already in `constants.py`)
- `name`: `New Tab Fx<major> <Mon>-<DD> Trainhop` (month abbrev from YYYYMMDD, e.g. `Jun-10`)
- `slug`: `newtab-<major>-<MMDD>-trainhop` (e.g. `newtab-153-0610-trainhop`)
- `targeting`: `newtabAddonVersion|versionCompare('<version>') >= 0`

### 3. File the GitHub issue

```
gh issue create --repo mozilla/experimenter \
  --title "[Targeting] newtab trainhop <version> targeting request" \
  --body "$(cat <<'EOF'
### What is the criteria you need to target based on?

This is to add advanced targeting such that experiments and rollouts can target New Tabs of version \`<version>\` and greater.

This will be very similar to previous targeting requests:

- https://github.com/mozilla/experimenter/issues/15414
- https://github.com/mozilla/experimenter/issues/14888
- https://github.com/mozilla/experimenter/issues/14577
- https://github.com/mozilla/experimenter/issues/14203

### Should the targeting include or exclude users?

Include users of the soon-to-be-released New Tab train-hop for Firefox <fx-major> users on the release channel.

### Additional Notes (optional)

*No response*
EOF
)"
```

The Jira sync footer is auto-added — leave it out. `gh issue create` prints the new issue
URL; capture the **issue number** from it for the next steps.

### 4. Create the branch

```
git checkout -b <issue-number>-train-hop-<version>
```

e.g. `15938-train-hop-153.4.20260610.40323`.

### 5. Add the target

Append the new config immediately after the most recent `FX_..._TRAINHOP` entry in
`experimenter/experimenter/targeting/constants.py`, copying its exact shape:

```python
FX_153_4_TRAINHOP = NimbusTargetingConfig(
    name="New Tab Fx153 Jun-10 Trainhop",
    slug="newtab-153-0610-trainhop",
    description=(
        "Desktop users having the New Tab 153.4.20260610.40323 train hop, "
        "which includes users of Fx151"
    ),
    targeting="newtabAddonVersion|versionCompare('153.4.20260610.40323') >= 0",
    desktop_telemetry="",
    sticky_required=False,
    is_first_run_required=False,
    application_choice_names=(Application.DESKTOP.name,),
)
```

Confirm the latest entry first: `grep -n "TRAINHOP = NimbusTargetingConfig" experimenter/experimenter/targeting/constants.py | tail`.
This is the only source file that changes.

### 6. Run ruff

From the `experimenter/` directory. Pull the ruff version the repo pins rather than
hardcoding it:

```
RUFF_SPEC=$(grep -m1 '^ruff = ' experimenter/pyproject.toml | sed -E 's/.*"\^?([0-9.]+)".*/\1/')
pipx run --spec "ruff==$RUFF_SPEC" ruff check experimenter/targeting/constants.py
pipx run --spec "ruff==$RUFF_SPEC" ruff format --check --diff experimenter/targeting/constants.py
```

### 7. Stage changes and draft the commit message

```
git add experimenter/experimenter/targeting/constants.py
```

Print this message — do NOT commit unless asked:

```
feat(nimbus): Add advanced targeting for newtab trainhop <version>
This commit adds new targeting for the <version> trainhop, which includes users of Fx<fx-major> on the release channel.

Fixes mozilla#<issue-number>
```

## Reference examples

PRs #15676, #15786, #15842 — each is a single ~14-line addition to `constants.py`.
