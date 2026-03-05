# Train-hop: Update Metrics

Generates updated runtime metrics JSON files for Beta and Release, cleans up stale files, and commits.

## Pre-condition

Working tree is clean on `main`.

## Steps

### 1. Run channel-metrics-diff

```bash
./mach newtab channel-metrics-diff --channel beta
./mach newtab channel-metrics-diff --channel release
```

### 2. Clean up stale runtime-metrics files

```bash
python3 <skill-scripts-dir>/cleanup_metrics.py
```

The script deletes `runtime-metrics-N.json` files where N is less than the current Nightly major version and reports what was deleted.

### 3. Review changes

Show the user a summary of changed, added, and deleted files in `browser/extensions/newtab/webext-glue/metrics/`.

### 4. File a bug

Read the major version from `browser/config/version.txt` (e.g. `147`), then run:

```bash
python3 <skill-scripts-dir>/file_bug.py \
  --summary "Update runtime-metrics for Firefox MAJOR_VERSION train-hop" \
  --blocks META_BUG_NUMBER
```

Omit `--blocks` if no meta bug number is available. Note the printed bug ID.

### 5. Create a branch, lint, commit, and submit

```bash
git checkout -b bug-BUG_NUMBER-update-metrics-trainhop
./mach lint browser/extensions/newtab/webext-glue/metrics/
git commit browser/extensions/newtab/webext-glue/metrics/ -m "Bug BUG_NUMBER - Update New Tab runtime metrics for train-hop r?#home-newtab-reviewers"
moz-phab submit -s
```

## Expected Result

A Phabricator revision is open for review. `git log --oneline -1` shows the metrics commit on the new branch.

## Troubleshooting

**Lint fails**
Read the error, fix the issue, and re-run before committing.

**moz-phab auth error**
Ask the user to run `moz-phab submit` manually and check their Phabricator token.
