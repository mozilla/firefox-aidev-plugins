# Train-hop: Create Confluence Page

Creates the `HNT VERSION Train Hop` tracking page in the FPS Confluence space.

## Steps

### 1. Create the page

Read the major version from `browser/config/version.txt` (e.g. `147`), then run:

```bash
python3 <skill-scripts-dir>/create_confluence_page.py \
  --version MAJOR_VERSION \
  --metabug-url https://bugzilla.mozilla.org/show_bug.cgi?id=META_BUG_NUMBER \
  --qa-ticket QA_TICKET_KEY \
  --xpi-cut XPI_CUT_DATE \
  --qa-handoff QA_HANDOFF_DATE \
  --release-date RELEASE_DATE \
  --relman "REL_MAN_CONTACT" \
  --qa-contact "QA_CONTACT"
```

Substitute values from the inputs collected at the start of the workflow. The script prompts for your Atlassian email and API token, then prints the page URL.

## Expected Result

The page is accessible at the printed URL under the Train Hops folder in the FPS space, with the summary, timeline, and empty tables pre-populated. The user fills in the "Features being tested" table manually.

## Troubleshooting

**HTTP 401**
Check that your email and API token are correct. Get a token at: https://id.atlassian.com/manage-profile/security/api-tokens

**HTTP 404**
Parent folder ID `1872035972` may have changed. Update `PARENT_PAGE_ID` in `scripts/create_confluence_page.py`.
