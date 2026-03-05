---
name: trainhop-bump-version
description: Bumps the newtab version in manifest.json after cutting a train-hop XPI release. Use when explicitly asked to "bump the newtab version after train-hop", "post-train-hop version bump", or "bump minor version for newtab". Optionally pass an existing Bugzilla bug number. Do NOT use for general version bumps or non-train-hop releases.
argument-hint: "[meta-bug-number] (optional)"
---

# Train-hop: Bump Minor Version

After a New Tab train-hop XPI release is cut, the version in `browser/extensions/newtab/manifest.json` must be bumped so the next release starts from a clean state.

## Important

Do not skip any steps. Complete every step in order before moving to the next.

## Steps

### 1. Read current version

Read `browser/extensions/newtab/manifest.json` and extract the `version` field (format: `MAJOR.MINOR.PATCH`).

### 2. Read current Nightly version

Read `browser/config/version.txt` and extract the major version number (e.g. `150` from `150.0a1`).

### 3. Compute new version

Compare the manifest MAJOR with the Nightly MAJOR:

- If they match (still on same Nightly): bump MINOR by 1, keep PATCH as 0
  - e.g. `149.2.0` → `149.3.0`
- If Nightly MAJOR is higher (train moved forward): use Nightly MAJOR, reset MINOR and PATCH to 0
  - e.g. manifest `149.2.0`, Nightly `150` → `150.0.0`

### 4. Get or file a bug

If $ARGUMENTS contains a bug number, use it and skip to step 5.

Otherwise, file a new bug via the Bugzilla REST API:

```bash
curl -s -X POST https://bugzilla.mozilla.org/rest/bug \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "'"$BUGZILLA_API_KEY"'",
    "product": "Firefox",
    "component": "New Tab Page",
    "summary": "Bump the minor version number of New Tab from OLD_VERSION to NEW_VERSION",
    "version": "Trunk",
    "op_sys": "All",
    "platform": "All",
    "blocks": [META_BUG_NUMBER]
  }'
```

Replace META_BUG_NUMBER with the meta bug number from $ARGUMENTS (omit the `blocks` field if no meta bug number was provided).

- If `BUGZILLA_API_KEY` is set in the environment, run this automatically and extract the `id` from the response.
- If `BUGZILLA_API_KEY` is not set, print the curl command (with values substituted) for the user to run, then wait for them to provide the bug number before continuing.

### 5. Edit manifest.json

Edit `browser/extensions/newtab/manifest.json`, updating the `version` field to the new version.

### 6. Lint

Run the linter on the manifest:

```bash
./mach lint --fix browser/extensions/newtab/manifest.json
```

If linting fails, fix the issue before proceeding.

### 7. Commit

Commit the change:

```bash
git commit browser/extensions/newtab/manifest.json -m "Bug BUG_NUMBER - Bump the newtab manifest version number r?#home-newtab-reviewers"
```

### 8. Submit for review

Run:

```bash
moz-phab submit -s
```

## Troubleshooting

**`BUGZILLA_API_KEY` not set**
Print the curl command with substituted values for the user to run manually, then ask them to provide the resulting bug number.

**Lint fails**
Read the error output, fix the issue in `manifest.json`, and re-run the linter before committing.

**`moz-phab submit` fails with auth error**
Ask the user to run `moz-phab submit` manually. They may need to re-authenticate with `moz-phab self-update` or check their Phabricator token.

**`moz-phab submit` fails with "no commit found"**
Verify the commit was created in step 7. Run `git log --oneline -3` to confirm.
