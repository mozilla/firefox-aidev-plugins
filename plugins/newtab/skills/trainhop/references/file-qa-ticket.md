# Train-hop: File QA Ticket

Creates a Jira ticket in the QA project to notify QA that the train-hop XPI is ready for testing.

## Steps

### 1. Create the ticket

Read the major version from `browser/config/version.txt` (e.g. `147`), then run:

```bash
python3 <skill-scripts-dir>/file_jira_ticket.py --version MAJOR_VERSION
```

The script prompts for your Atlassian email and API token and prints the ticket key (e.g. `QA-1234`). Note it for the Confluence page.

## Expected Result

The ticket is visible at `https://mozilla-hub.atlassian.net/browse/QA-XXXX` with summary `Testing New Tab train-hop for Firefox MAJOR_VERSION Release`.

## Troubleshooting

**HTTP 401**
Check that your email and API token are correct. Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens

**HTTP 400**
Issue type ID `11461` may have changed. Update `ISSUE_TYPE_ID` in `scripts/file_jira_ticket.py`.
