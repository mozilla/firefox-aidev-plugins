---
name: trainhop-update-locales
description: Updates the New Tab locale files for a train-hop release. Use when asked to "update train-hop locales", "run update-locales for train-hop", or "prepare locales for train-hop". Do NOT use for general locale changes unrelated to train-hopping.
argument-hint: "[meta-bug-number] (optional)"
---

# Train-hop: Update Locales

Updates the en-US `newtab.ftl` and pulls the latest translations for all supported locales, then commits the result.

## Important

Do not skip any steps. Complete each step fully before moving to the next.

## Steps

### 1. Read current Nightly version

Read `browser/config/version.txt` and extract the major version number (e.g. `147` from `147.0a1`). This will be used in the bug summary.

### 2. Update locales

```bash
./mach newtab update-locales
```

### 3. Review the locales report

```bash
./mach newtab locales-report
```

Display the full report to the user. Call out any locales with **pending** strings — these may require a conversation with Product Management before proceeding, as they could block the train-hop for affected regions.

Wait for the user to confirm it is safe to continue before proceeding.

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
    "summary": "Update locales for Firefox MAJOR_VERSION train-hop",
    "version": "Trunk",
    "op_sys": "All",
    "platform": "All",
    "blocks": [META_BUG_NUMBER]
  }'
```

Replace MAJOR_VERSION with the Nightly major version read in step 1 (e.g. `147`), and META_BUG_NUMBER with the meta bug number from $ARGUMENTS (omit the `blocks` field if no meta bug number was provided).

- If `BUGZILLA_API_KEY` is set in the environment, run this automatically and extract the `id` from the response.
- If `BUGZILLA_API_KEY` is not set, print the curl command (with values substituted) for the user to run, then wait for them to provide the bug number before continuing.

### 5. Lint

```bash
./mach lint browser/extensions/newtab/
```

If linting fails, fix the issue before proceeding.

### 6. Commit

```bash
git commit browser/extensions/newtab/ -m "Bug BUG_NUMBER - Update locales for Firefox MAJOR_VERSION train-hop r?#home-newtab-reviewers"
```

### 7. Submit for review

```bash
moz-phab submit
```

## Troubleshooting

**Pending strings in locales report**
Stop and inform the user which locales have pending strings. They should consult Product Management before proceeding, as train-hopping may need to be blocked for affected regions or gated via Nimbus feature flags.

**mach command not found**
Ensure you are running from the root of the Firefox source tree.

**Lint fails**
Read the error output, fix the issue, and re-run the linter before committing.

**moz-phab submit fails with auth error**
Ask the user to run `moz-phab submit` manually and check their Phabricator token.
