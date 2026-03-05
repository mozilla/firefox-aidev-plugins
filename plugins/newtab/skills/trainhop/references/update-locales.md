# Train-hop: Update Locales

Updates `newtab.ftl` and pulls the latest translations for all supported locales.

## Pre-condition

Working tree is clean on `main`.

## Steps

### 1. Update locales

```bash
./mach newtab update-locales
```

### 2. Review the locales report

```bash
./mach newtab locales-report
```

Display the full report. Call out any locales with **pending** strings — these may need a conversation with Product Management before proceeding, as they could block the train-hop for affected regions.

Wait for the user to confirm it is safe to continue.

### 3. File a bug

Read the major version from `browser/config/version.txt` (e.g. `147`), then run:

```bash
python3 <skill-scripts-dir>/file_bug.py \
  --summary "Update locales for Firefox MAJOR_VERSION train-hop" \
  --blocks META_BUG_NUMBER
```

Omit `--blocks` if no meta bug number is available. Note the printed bug ID.

### 4. Create a branch, lint, commit, and submit

```bash
git checkout -b bug-BUG_NUMBER-update-locales-trainhop
./mach lint browser/extensions/newtab/
git commit browser/extensions/newtab/ -m "Bug BUG_NUMBER - Update locales for Firefox MAJOR_VERSION train-hop r?#home-newtab-reviewers"
moz-phab submit
```

## Expected Result

A Phabricator revision is open for review. `git log --oneline -1` shows the locales commit on the new branch.

## Troubleshooting

**Pending strings in locales report**
Stop and inform the user which locales are affected. Consult Product Management — the train-hop may need to be blocked for those regions or gated via Nimbus.

**Lint fails**
Read the error, fix the issue, and re-run before committing.

**moz-phab auth error**
Ask the user to run `moz-phab submit` manually and check their Phabricator token.
