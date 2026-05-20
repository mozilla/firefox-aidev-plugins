# Train-hop: File QA Ticket

Creates a Jira ticket in the QA project to notify QA that the train-hop XPI is ready for testing.

This step is run **after** the Confluence page is created (so the page URL can be linked in the ticket).

## Steps

### 1. Create the ticket via the Atlassian MCP

Use the `mcp__atlassian__createJiraIssue` tool. Read the major version from `browser/config/version.txt` (e.g. `151`).

**Required parameters**:

- `cloudId`: `mozilla-hub.atlassian.net`
- `projectKey`: `QA`
- `issueTypeName`: `Functional`
- `summary`: `Testing New Tab train-hop for Firefox MAJOR_VERSION Release`
- `description`: timeline blurb (see template below) — pass with `contentFormat: "markdown"`
- `assignee_account_id`: the QA contact's Atlassian accountId (use `mcp__atlassian__lookupJiraAccountId` if unknown)
- `additional_fields`: see customfield mapping below

**Description template** (substitute the QA Handoff weekday and date):

```
On {QA_HANDOFF_WEEKDAY}, {QA_HANDOFF_MONTH_DAY}, two days after the Firefox MAJOR_VERSION Release, the New Tab team aims to perform a train-hop.

Note: We are holding cutting the release for a few different features. If we do not have those features ready, we will shift the entire timeline to accommodate.
```

**Customfield mapping (`additional_fields`)** — mirrors the QA-4752 / QA-5234 reference tickets:

```json
{
  "labels": ["QA:Desktop", "QA:High"],
  "duedate": "QA_SIGNOFF_DATE",
  "customfield_10134": {"value": "Front End"},
  "customfield_10137": "Testing New Tab train-hop for Firefox MAJOR_VERSION Release",
  "customfield_10138": "FEATURE_OWNER_NAME",
  "customfield_10139": {
    "type": "doc", "version": 1,
    "content": [{"type": "paragraph", "content": [
      {"type": "inlineCard", "attrs": {"url": "CONFLUENCE_PAGE_URL"}}
    ]}]
  },
  "customfield_10140": {
    "type": "doc", "version": 1,
    "content": [{"type": "paragraph", "content": [
      {"type": "inlineCard", "attrs": {"url": "CONFLUENCE_PAGE_URL"}},
      {"type": "text", "text": " "},
      {"type": "hardBreak"},
      {"type": "inlineCard", "attrs": {"url": "METABUG_URL"}}
    ]}]
  },
  "customfield_10147": [{"value": "Desktop"}],
  "customfield_10151": {"value": "System Add-on"},
  "customfield_10155": {"value": "FxMAJOR_VERSION"},
  "customfield_10749": "METABUG_URL"
}
```

Substitute:
- `MAJOR_VERSION` — Firefox major version (e.g. `151`)
- `QA_SIGNOFF_DATE` — `YYYY-MM-DD` of QA sign-off (becomes the ticket's due date)
- `FEATURE_OWNER_NAME` — name of the Feature Owner (typically the train-hop conductor running the workflow)
- `CONFLUENCE_PAGE_URL` — full URL of the Confluence page created in the previous step
- `METABUG_URL` — full Bugzilla URL: `https://bugzilla.mozilla.org/show_bug.cgi?id=BUG_ID`

### 2. Note the ticket key

The MCP response contains `key` (e.g. `QA-5234`). Pass it to the next step (Confluence page update).

## Expected Result

The ticket is visible at `https://mozilla-hub.atlassian.net/browse/QA-XXXX` with summary `Testing New Tab train-hop for Firefox MAJOR_VERSION Release`, assigned to the QA contact, and with the Confluence page linked in customfield_10139 (Technical Documentation).

## Customfield reference

| Field ID | Purpose | Value shape |
|---|---|---|
| `customfield_10134` | Engineering Team | `{"value": "Front End"}` |
| `customfield_10137` | Test Suite (mirrors summary) | string |
| `customfield_10138` | Feature Owner | string (name) |
| `customfield_10139` | Technical Documentation link | ADF doc with `inlineCard` of Confluence URL |
| `customfield_10140` | Test Plan links | ADF doc with `inlineCard`s of Confluence + metabug |
| `customfield_10147` | Product | `[{"value": "Desktop"}]` |
| `customfield_10151` | Shipping Method | `{"value": "System Add-on"}` |
| `customfield_10155` | Firefox Version | `{"value": "FxXXX"}` |
| `customfield_10749` | Meta Bug | plain URL string |

## Troubleshooting

**MCP `createJiraIssue` denied by classifier**
Re-prompt the user to authorize the call — the workflow explicitly creates a Jira ticket on the user's behalf.

**Invalid issue type or customfield**
Issue type ID for Functional is `11461`. If the MCP rejects `issueTypeName: "Functional"`, fall back to passing the ID via `additional_fields.issuetype.id`. If customfield IDs have drifted, fetch a recent reference ticket (e.g. `QA-5234`) via `mcp__atlassian__getJiraIssue` with explicit `fields` to confirm the schema.

**Legacy fallback**
If the MCP is unavailable, the original Python script (`scripts/file_jira_ticket.py`) still works given `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_NAME` env vars.
