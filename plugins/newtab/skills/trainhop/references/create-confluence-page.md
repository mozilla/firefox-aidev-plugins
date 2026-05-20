# Train-hop: Create Confluence Page

Creates the `HNT VERSION Train Hop` tracking page in the FPS Confluence space.

This step is run **before** the QA ticket is filed (because the QA ticket needs the page URL). Once the QA ticket exists, this page is then updated to swap the `QA-TBD` placeholder for the real ticket link.

## Constants

- **Cloud ID**: `mozilla-hub.atlassian.net`
- **FPS space ID**: `12484637`
- **Parent folder ID** ("HNT Train Hop Releases"): `1872035972`

## Steps

### 1. Create the page via the Atlassian MCP

Use `mcp__atlassian__createConfluencePage` with `contentFormat: "adf"` so that date macros and `@mention` nodes render natively. Read the major version from `browser/config/version.txt`.

**Required parameters**:

- `cloudId`: `mozilla-hub.atlassian.net`
- `spaceId`: `12484637`
- `parentId`: `1872035972`
- `title`: `HNT MAJOR_VERSION Train Hop`
- `contentFormat`: `adf`
- `body`: ADF document (see template below)

### 2. Body template (ADF)

Compose an ADF document with this structure. Substitute the placeholders before sending.

```json
{
  "type": "doc",
  "version": 1,
  "content": [
    {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Summary:"}]},
    {"type": "bulletList", "content": [
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "Meta Bug: "},
        {"type": "inlineCard", "attrs": {"url": "METABUG_URL"}}
      ]}]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "QA Bug: QA-TBD (will update once filed)"}
      ]}]},
      {"type": "listItem", "content": [
        {"type": "paragraph", "content": [{"type": "text", "text": "Timeline:"}]},
        {"type": "bulletList", "content": [
          {"type": "listItem", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "XPI Cut: "},
            {"type": "date", "attrs": {"timestamp": "XPI_CUT_TIMESTAMP_MS"}}
          ]}]},
          {"type": "listItem", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "QA Handoff: "},
            {"type": "date", "attrs": {"timestamp": "QA_HANDOFF_TIMESTAMP_MS"}}
          ]}]},
          {"type": "listItem", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "QA Sign-off: "},
            {"type": "date", "attrs": {"timestamp": "QA_SIGNOFF_TIMESTAMP_MS"}}
          ]}]},
          {"type": "listItem", "content": [{"type": "paragraph", "content": [
            {"type": "text", "text": "Release: "},
            {"type": "date", "attrs": {"timestamp": "RELEASE_TIMESTAMP_MS"}}
          ]}]}
        ]}
      ]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "Rel Man contact: "},
        {"type": "mention", "attrs": {"id": "RELMAN_ACCOUNT_ID", "text": "@RELMAN_NAME"}}
      ]}]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "QA contact: "},
        {"type": "mention", "attrs": {"id": "QA_ACCOUNT_ID", "text": "@QA_NAME"}}
      ]}]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "Conductor: "},
        {"type": "mention", "attrs": {"id": "CONDUCTOR_ACCOUNT_ID", "text": "@CONDUCTOR_NAME"}}
      ]}]}
    ]},
    {"type": "heading", "attrs": {"level": 4}, "content": [{"type": "text", "text": "Helpful Links"}]},
    {"type": "bulletList", "content": [
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "See documentation: "},
        {"type": "inlineCard", "attrs": {"url": "https://mozilla-hub.atlassian.net/wiki/spaces/FPS/pages/1785135275"}}
      ]}]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "See check-list: "},
        {"type": "inlineCard", "attrs": {"url": "https://mozilla-hub.atlassian.net/wiki/x/kABgag"}}
      ]}]},
      {"type": "listItem", "content": [{"type": "paragraph", "content": [
        {"type": "text", "text": "Real-time Train Hop Adoption Graph", "marks": [{"type": "link", "attrs": {"href": "https://sql.telemetry.mozilla.org/dashboard/new-tab-train-hop-add-on-uptake-dashboard"}}]}
      ]}]}
    ]},
    {"type": "rule"},
    {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "Features being tested:"}]},
    {"type": "paragraph", "content": [{"type": "text", "text": "These are the experiments/tickets that are planned as part of this release. They can be required or optional."}]},
    {"type": "table", "content": [
      {"type": "tableRow", "content": [
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Jira Ticket / Summary", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Product Owner", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Priority", "marks": [{"type": "strong"}]}]}]}
      ]},
      {"type": "tableRow", "content": [
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]}
      ]}
    ]},
    {"type": "heading", "attrs": {"level": 3}, "content": [{"type": "text", "text": "QA Verified Bugs/Patches"}]},
    {"type": "table", "content": [
      {"type": "tableRow", "content": [
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Bug", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Summary", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Landing Status", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "QA Status", "marks": [{"type": "strong"}]}]}]}
      ]},
      {"type": "tableRow", "content": [
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]}
      ]}
    ]},
    {"type": "heading", "attrs": {"level": 3}, "content": [
      {"type": "text", "text": "Shims added for "},
      {"type": "text", "text": "@backward-compat", "marks": [{"type": "code"}]}
    ]},
    {"type": "table", "content": [
      {"type": "tableRow", "content": [
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Bug Link", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Title", "marks": [{"type": "strong"}]}]}]},
        {"type": "tableHeader", "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Notes", "marks": [{"type": "strong"}]}]}]}
      ]},
      {"type": "tableRow", "content": [
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]},
        {"type": "tableCell", "content": [{"type": "paragraph"}]}
      ]}
    ]}
  ]
}
```

### 3. Placeholder substitutions

- `MAJOR_VERSION` — Firefox major version (e.g. `151`)
- `METABUG_URL` — `https://bugzilla.mozilla.org/show_bug.cgi?id=BUG_ID`
- `*_TIMESTAMP_MS` — Unix epoch milliseconds at UTC midnight for each date. Convert `YYYY-MM-DD` with e.g. `python3 -c "import datetime;print(int(datetime.datetime(YYYY,MM,DD,tzinfo=datetime.timezone.utc).timestamp()*1000))"`.
- `RELMAN_ACCOUNT_ID` / `QA_ACCOUNT_ID` / `CONDUCTOR_ACCOUNT_ID` — Atlassian accountIds; resolve with `mcp__atlassian__lookupJiraAccountId` if not known.
- `*_NAME` — the user's display name (prefixed with `@`, e.g. `@Donal Meehan`).

Common accountIds (FYI, verify before use):
- Valentin Bandac (QA): `6310ac8255b0a9e29f1af16d`
- Maxx Crawford: `5cd0455cdfe2e60fdd10e002`

### 4. Note the page ID and URL

The MCP response contains `id` and `_links.webui`. Pass them to the next step (file QA ticket).

### 5. Update the page after the QA ticket is filed

Once the QA ticket key is known, use `mcp__atlassian__updateConfluencePage` to replace the `QA-TBD` placeholder with a real link. The simplest approach is to re-send the same ADF body with the placeholder swapped for:

```json
{"type": "paragraph", "content": [
  {"type": "text", "text": "QA Bug: "},
  {"type": "text", "text": "QA-XXXX: Testing New Tab train-hop for Firefox MAJOR_VERSION Release", "marks": [{"type": "link", "attrs": {"href": "https://mozilla-hub.atlassian.net/browse/QA-XXXX"}}]}
]}
```

Pass `versionMessage: "Fill in QA ticket reference (QA-XXXX)"` so the page history is self-documenting.

## Expected Result

The page is accessible under "HNT Train Hop Releases" in the FPS space with the summary, timeline (using interactive date macros), and contact `@mention`s. The "Features being tested" / "QA Verified Bugs/Patches" / "Shims" tables are empty and filled in by the conductor.

## Troubleshooting

**MCP returns 404 on `parentId`**
The "HNT Train Hop Releases" folder may have moved. Search with `mcp__atlassian__searchConfluenceUsingCql` for `space = FPS AND title ~ "Train Hop"` and find the folder (type `folder`) — update the constant at the top of this file.

**Date macros render as plain text**
Confirm `contentFormat: "adf"` was passed. Markdown content cannot express `date` or `mention` nodes; they will be flattened to plain text.

**Mention shows as `@unknown`**
The accountId is wrong. Resolve via `mcp__atlassian__lookupJiraAccountId` and try again.

**Legacy fallback**
If the MCP is unavailable, the original Python script (`scripts/create_confluence_page.py`) still works but emits the older plain-text template (no date macros, no `@mention`s, no QA Sign-off, no Conductor row).
