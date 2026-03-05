---
name: trainhop-update-metrics
description: Updates the New Tab metrics and pings JSON files for a train-hop release. Use when asked to "update train-hop metrics", "run channel-metrics-diff", or "prepare metrics for train-hop". Do NOT use for general metrics changes unrelated to train-hopping.
argument-hint: "[meta-bug-number] (optional)"
---

# Train-hop: Update Metrics

Generates updated runtime metrics JSON files for the Beta and Release channels, cleans up stale files, and commits the result.

## Important

Do not skip any steps. Complete each step fully before moving to the next.

## Steps

### 1. Run channel-metrics-diff for both channels

Run both commands:

```bash
./mach newtab channel-metrics-diff --channel beta
./mach newtab channel-metrics-diff --channel release
```

### 2. Clean up stale runtime-metrics files

List the files in `browser/extensions/newtab/webext-glue/metrics/`:

```bash
ls browser/extensions/newtab/webext-glue/metrics/
```

Read `browser/config/version.txt` to get the current release version major number (e.g. `146` from `146.0`).

Delete any `runtime-metrics-N.json` file where N is less than the current release major version. Do not delete empty files — a file containing `{"metrics": {}, "pings": {}}` should be kept if its version is current.

### 3. Review changes

Show the user a summary of what changed (new files, deleted files, modified files) in `browser/extensions/newtab/webext-glue/metrics/`.

### 4. Lint

```bash
./mach lint browser/extensions/newtab/webext-glue/metrics/
```

If linting fails, fix the issue before proceeding.

### 5. Get or file a bug

If $ARGUMENTS contains a bug number, use it and skip to step 6.

Otherwise, file a new bug via the Bugzilla REST API:

```bash
curl -s -X POST https://bugzilla.mozilla.org/rest/bug \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "'"$BUGZILLA_API_KEY"'",
    "product": "Firefox",
    "component": "New Tab Page",
    "summary": "Update runtime-metrics for Firefox MAJOR_VERSION train-hop",
    "version": "Trunk",
    "op_sys": "All",
    "platform": "All",
    "blocks": [META_BUG_NUMBER]
  }'
```

Replace MAJOR_VERSION with the Nightly major version read in step 2 (e.g. `147`), and META_BUG_NUMBER with the meta bug number from $ARGUMENTS (omit the `blocks` field if no meta bug number was provided).

- If `BUGZILLA_API_KEY` is set in the environment, run this automatically and extract the `id` from the response.
- If `BUGZILLA_API_KEY` is not set, print the curl command (with values substituted) for the user to run, then wait for them to provide the bug number before continuing.

### 6. Commit

```bash
git commit browser/extensions/newtab/webext-glue/metrics/ -m "Bug BUG_NUMBER - Update New Tab runtime metrics for train-hop r?#home-newtab-reviewers"
```

### 7. Submit for review

```bash
moz-phab submit -s
```

## Troubleshooting

**mach command not found**
Ensure you are running from the root of the Firefox source tree.

**Lint fails**
Read the error output, fix the issue, and re-run the linter before committing.

**moz-phab submit fails with auth error**
Ask the user to run `moz-phab submit` manually and check their Phabricator token.
