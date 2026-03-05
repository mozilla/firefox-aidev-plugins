# Credential Setup

The train-hop workflow requires the following credentials. Scripts will prompt for them at runtime — nothing needs to be stored.

## Bugzilla API Key

Used to file Bugzilla bugs automatically.

1. Go to https://bugzilla.mozilla.org and sign in
2. Click your name → **Preferences** → **API Keys**
3. Enter a description (e.g. "train-hop automation") and click **Generate Key**
4. Copy the key — you will be prompted for it when the script runs

## Atlassian Credentials

Used to create Jira tickets and Confluence pages.

**Email**: your Mozilla email address (e.g. `you@mozilla.com`)

**API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Enter a label (e.g. "train-hop") and copy the token
