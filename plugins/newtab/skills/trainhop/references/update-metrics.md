# Train-hop: Update Metrics

Generates updated runtime metrics JSON files for Beta and Release, cleans up stale files, and commits.

## Pre-condition

Working tree is clean on `main`.

## Version numbers (read this first)

`browser/config/version.txt` holds the **Nightly** major version (call it `M`, e.g. `150`). The runtime-metrics files are named after the **channel** version, not the Nightly version:

- `channel-metrics-diff --channel beta` writes/updates `runtime-metrics-(M-1).json` (Beta = `149`)
- `channel-metrics-diff --channel release` writes/updates `runtime-metrics-(M-2).json` (Release = `148`)

So during a train-hop while Nightly is `150`, seeing a `runtime-metrics-149.json` (Beta) and `runtime-metrics-148.json` (Release) is **expected and correct** — it is *not* a bug that no `runtime-metrics-150.json` is produced. Do not "fix" the version by renaming these files.

## Steps

### 1. Run channel-metrics-diff

```bash
./mach newtab channel-metrics-diff --channel beta
./mach newtab channel-metrics-diff --channel release
```

Each command regenerates the metrics JSON for its channel version (see above).

### 2. Normalize and clean up

```bash
./mach lint --fix browser/extensions/newtab/webext-glue/metrics/   # normalize
python3 <skill-scripts-dir>/cleanup_metrics.py --dry-run           # preview stale-file deletions
python3 <skill-scripts-dir>/cleanup_metrics.py                     # then delete
```

- `lint --fix` normalizes the regenerated files. `channel-metrics-diff` frequently rewrites them with only formatting/ordering differences, which `lint --fix` reverts completely — so it is normal for the regenerated files to end up unchanged.
- `cleanup_metrics.py` deletes `runtime-metrics-N.json` files where N is **less than the release-channel version** (Nightly major `M` − 2), keeping the release, beta, and nightly files. Confirm the cutoff with `--dry-run` first; pass `--release-version N` if the train model differs this cycle.

### 3. Check whether there's anything to land

```bash
git status --short browser/extensions/newtab/webext-glue/metrics/
```

- **Empty output → no metrics changes this cycle.** Stop here: do **not** file a bug, create a branch, or submit. Report to the user that the runtime metrics are already up to date (nothing to land).
- **Changes remain** (modified metrics files and/or a deleted stale file) → continue to step 4.

### 4. Review changes

Show the user a summary of the changed, added, and deleted files in `browser/extensions/newtab/webext-glue/metrics/`.

### 5. File a bug

Use the `TARGET_VERSION` (release target) from the orchestrator — see SKILL.md → "Determine the train-hop target version". This is the release label (`M − 2`), distinct from the per-channel metrics *file* versions described above. Then run:

```bash
python3 <skill-scripts-dir>/file_bug.py \
  --summary "Update runtime-metrics for Firefox TARGET_VERSION train-hop" \
  --blocks META_BUG_NUMBER
```

Omit `--blocks` if no meta bug number is available. Note the printed bug ID.

### 6. Create a branch, commit, and submit

The files were already normalized in step 2, so just branch, commit, and submit:

```bash
git checkout -b bug-BUG_NUMBER-update-metrics-trainhop
git commit browser/extensions/newtab/webext-glue/metrics/ -m "Bug BUG_NUMBER - Update New Tab runtime metrics for train-hop r?#home-newtab-reviewers"
moz-phab submit -s
```

## Expected Result

Either: a Phabricator revision is open for review and `git log --oneline -1` shows the metrics commit on the new branch — **or**, if step 3 found no changes, nothing was filed or committed and the user was told the runtime metrics are already up to date.

## Troubleshooting

**`channel-metrics-diff` errors or produces no output**
Confirm your build is up to date (`./mach build` may be required after pulling) and that you are running from the repo root. Re-run the single failing channel rather than both.

**`cleanup_metrics.py` wants to delete a file you expected to keep**
Re-check the cutoff line it prints ("Release channel version: N"). If Nightly−2 is wrong for this cycle, re-run with `--release-version N`. Nothing is deleted under `--dry-run`.

**Lint fails**
Read the error, fix the issue, and re-run before committing.

**moz-phab auth error**
Ask the user to run `moz-phab submit` manually and check their Phabricator token.
