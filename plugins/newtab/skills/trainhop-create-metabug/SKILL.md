---
name: trainhop-create-metabug
description: Creates the Bugzilla meta bug for a New Tab train-hop release. Use when asked to "create the train-hop metabug" or "file the train-hop meta bug". Returns the meta bug number for use by other train-hop skills.
---

# Train-hop: Create Meta Bug

Files the Bugzilla meta bug that tracks the full train-hop release. All other bugs filed during the train-hop process should block this meta bug.

## Important

Do not skip any steps. Complete each step fully before moving to the next.

## Steps

### 1. Read current Nightly version

Read `browser/config/version.txt` and extract the major version number (e.g. `147` from `147.0a1`).

### 2. File the meta bug

```bash
curl -s -X POST https://bugzilla.mozilla.org/rest/bug \
  -H "Content-Type: application/json" \
  -d '{
    "api_key": "'"$BUGZILLA_API_KEY"'",
    "product": "Firefox",
    "component": "New Tab Page",
    "summary": "[meta] Firefox MAJOR_VERSION train-hop metabug",
    "version": "Trunk",
    "op_sys": "All",
    "platform": "All",
    "type": "task",
    "keywords": ["meta"]
  }'
```

Replace MAJOR_VERSION with the Nightly major version from step 1 (e.g. `147`).

- If `BUGZILLA_API_KEY` is set in the environment, run this automatically and extract the `id` from the response.
- If `BUGZILLA_API_KEY` is not set, print the curl command (with MAJOR_VERSION substituted) for the user to run, then wait for them to provide the bug number before continuing.

### 3. Display the meta bug number

Print the meta bug number clearly so the user can reference it. All subsequent bugs filed during this train-hop should block this meta bug.

## Troubleshooting

**`BUGZILLA_API_KEY` not set**
Print the curl command with MAJOR_VERSION substituted for the user to run manually, then ask them to provide the resulting bug number.

**API returns an error**
Display the full error response. Common causes: invalid API key, or missing required fields.
