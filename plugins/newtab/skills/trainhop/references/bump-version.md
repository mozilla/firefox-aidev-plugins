# Train-hop: Bump Minor Version

Bumps the version in `manifest.json` after the XPI is cut, so Nightly clients prefer the built-in New Tab over the train-hopped one on next update.

## Pre-condition

Working tree is clean on `main`. The XPI has already been built and signed via ShipIt.

## Steps

### 1. Compute and apply new version

```bash
python3 <skill-scripts-dir>/bump_version.py
```

The script reads `manifest.json` and `browser/config/version.txt`, computes the new version, writes it to `manifest.json`, and prints `OLD_VERSION → NEW_VERSION`. Note both — used in the commit message.

### 2. File a bug

```bash
python3 <skill-scripts-dir>/file_bug.py \
  --summary "Bump the minor version number of New Tab from OLD_VERSION to NEW_VERSION" \
  --blocks META_BUG_NUMBER
```

Omit `--blocks` if no meta bug number is available. Note the printed bug ID.

### 3. Create a branch, lint, commit, and submit

```bash
git checkout -b bug-BUG_NUMBER-bump-newtab-version-trainhop
./mach lint --fix browser/extensions/newtab/manifest.json
git commit browser/extensions/newtab/manifest.json -m "Bug BUG_NUMBER - Bump the newtab manifest version number r?#home-newtab-reviewers"
moz-phab submit -s
```

## Expected Result

`browser/extensions/newtab/manifest.json` `version` field reads `NEW_VERSION`. A Phabricator revision is open for review. `git log --oneline -1` shows the bump commit on the new branch.

## Troubleshooting

**Lint fails**
Read the error, fix the issue in `manifest.json`, and re-run before committing.

**moz-phab fails with "no commit found"**
Run `git log --oneline -3` to confirm the commit was created before retrying.
