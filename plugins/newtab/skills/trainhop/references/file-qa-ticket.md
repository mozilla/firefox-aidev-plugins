# Train-hop: File QA Ticket

Creates a Jira ticket in the QA project to notify QA that the train-hop XPI is ready for testing.

This step is run **after** the Confluence page is created (so the page URL can be linked in the ticket). Filing this ticket **notifies QA** — only run it when you actually want to hand off.

> **Tool prefix:** tool names below are written `${MCP}<tool>`, where `${MCP}` is your Atlassian MCP prefix (`mcp__plugin_atlassian_atlassian__` for the official plugin). See `references/credentials.md` → "Tool prefix (`${MCP}`)" to resolve it.

## Steps

### 1. Create the ticket

Use `${MCP}createJiraIssue`. Use the `TARGET_VERSION` (release target) from the orchestrator — see SKILL.md → "Determine the train-hop target version". The `customfield_10155` "Target release" select takes the **major component only** (e.g. `Fx152`, even if `TARGET_VERSION` is `152.0.5`).

**Parameters**:

- `cloudId`: `mozilla-hub.atlassian.net`
- `projectKey`: `QA`
- `issueTypeName`: `Functional` (id `11461`)
- `summary`: `Testing New Tab train-hop for Firefox TARGET_VERSION Release`
- `assignee_account_id`: the QA contact's accountId (default Valentin Bandac `6310ac8255b0a9e29f1af16d`; resolve others via `${MCP}lookupJiraAccountId`)
- `additional_fields`: see below
- No `description` — real train-hop tickets leave it empty.

**`additional_fields`** (field IDs, display names, and relevant train-hop values):

```json
{
  "labels": ["QA:Desktop", "QA:High"],
  "duedate": "QA_SIGNOFF_DATE",
  "customfield_10134": {"value": "New Tab"},
  "customfield_10137": "Testing New Tab train-hop for Firefox TARGET_VERSION Release",
  "customfield_10138": "FEATURE_OWNER_NAME",
  "customfield_10139": {
    "type": "doc", "version": 1,
    "content": [{"type": "paragraph", "content": [
      {"type": "inlineCard", "attrs": {"url": "CONFLUENCE_PAGE_URL"}}
    ]}]
  },
  "customfield_10140": {
    "type": "doc", "version": 1,
    "content": [
      {"type": "paragraph", "content": [{"type": "inlineCard", "attrs": {"url": "CONFLUENCE_PAGE_URL"}}]},
      {"type": "paragraph", "content": [{"type": "inlineCard", "attrs": {"url": "NIMBUS_ROLLOUT_URL"}}]}
    ]
  },
  "customfield_10147": [{"value": "Desktop"}],
  "customfield_10151": {"value": "System Add-on"},
  "customfield_10155": {"value": "Fx152"}
}
```

Substitute:
- `TARGET_VERSION` — release-target version (e.g. `152.0.5`); `Fx` uses the major only (`Fx152`)
- `QA_SIGNOFF_DATE` — `YYYY-MM-DD` of QA sign-off (the ticket's due date)
- `FEATURE_OWNER_NAME` — the train-hop conductor's name (Feature Owners)
- `CONFLUENCE_PAGE_URL` — the page from the previous step
- `NIMBUS_ROLLOUT_URL` — the Experimenter/Nimbus staging rollout URL. If the Nimbus recipe step was skipped, omit that second paragraph from `customfield_10140`.

### 2. Note the ticket key

The response contains `key` (e.g. `QA-XXXX`). Pass it to the next step (Confluence page update).

## Customfield reference

| Field ID | Display name | Value shape |
|---|---|---|
| `customfield_10134` | Engineering team | `{"value": "New Tab"}` |
| `customfield_10137` | Feature name | string (mirrors summary) |
| `customfield_10138` | Feature Owners | string (conductor name) |
| `customfield_10139` | Link to Technical Documentation | ADF doc with `inlineCard` of Confluence URL |
| `customfield_10140` | Relevant Links | ADF doc, one paragraph per `inlineCard`: Confluence page + Nimbus rollout |
| `customfield_10147` | Product | `[{"value": "Desktop"}]` |
| `customfield_10151` | Shipping Method | `{"value": "System Add-on"}` |
| `customfield_10155` | Target release | `{"value": "Fx152"}` (major only) |
| `customfield_10749` | Bugs to be filed at | left null |

## Expected Result

The ticket is at `https://mozilla-hub.atlassian.net/browse/QA-XXXX` with summary `Testing New Tab train-hop for Firefox TARGET_VERSION Release`, assigned to the QA contact, `QA:Desktop`/`QA:High` labels, and the Confluence page linked in Technical Documentation + Relevant Links.

## Troubleshooting

**Invalid select value on a customfield**
`customfield_10134`/`10147`/`10151`/`10155` are single-select — the value must be an exact allowed option. If one is rejected, find the most recent train-hop QA ticket with `${MCP}searchJiraIssuesUsingJql` (`project = QA AND summary ~ "train-hop" ORDER BY created DESC`, take the first result) and inspect its fields with `${MCP}getJiraIssue`.

**Issue type rejected**
If `issueTypeName: "Functional"` fails, pass the id via `additional_fields.issuetype.id = "11461"`.

**If the Atlassian MCP is unavailable**
Create the ticket manually in the Jira UI: open the most recent train-hop ticket, use **••• → Clone**, and update the summary, version, dates, and links.
