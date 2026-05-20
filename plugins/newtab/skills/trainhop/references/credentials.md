# Credential Setup

The train-hop workflow has two paths for Jira/Confluence:

- **Preferred** — the Atlassian MCP plugin (OAuth, no token to manage). See [Atlassian MCP plugin](#atlassian-mcp-plugin) below.
- **Legacy** — direct REST API calls from the Python scripts in `scripts/`, which require an email + API token. See [Atlassian API token (legacy)](#atlassian-api-token-legacy) below.

Bugzilla still uses a personal API key (no MCP equivalent yet).

## Bugzilla API Key

Used by `scripts/file_bug.py` to file the meta bug.

1. Go to https://bugzilla.mozilla.org and sign in
2. Click your name → **Preferences** → **API Keys**
3. Enter a description (e.g. "train-hop automation") and click **Generate Key**
4. Copy the key. Either export it as `BUGZILLA_API_KEY` in your shell (recommended: store in an untracked file like `.mozconfig-env` at the repo root and `set -a; source .mozconfig-env; set +a` before running the workflow), or let the script prompt for it interactively.

## Atlassian MCP plugin

The Atlassian MCP plugin is published in the **official Anthropic marketplace** (`claude-plugins-official`), which is registered automatically when Claude Code starts. See the [Discover plugins → External integrations](https://code.claude.com/docs/en/discover-plugins#external-integrations) docs for the full list.

### Install

From inside Claude Code, run:

```
/plugin install atlassian@claude-plugins-official
```

Then reload so the new MCP server is picked up:

```
/reload-plugins
```

If Claude Code reports the plugin is not found, refresh the marketplace first and retry:

```
/plugin marketplace update claude-plugins-official
/plugin install atlassian@claude-plugins-official
```

### Authenticate

On first use, the plugin walks you through an OAuth flow against your Mozilla Atlassian workspace (`mozilla-hub.atlassian.net`). Approve the requested scopes (read/write for Jira and Confluence). No tokens are stored locally — Claude Code manages the OAuth session.

### Verify

After install + reload, the `mcp__atlassian__*` tools should be available. A quick smoke test from Claude:

> List the spaces I can access in Confluence (use `mcp__atlassian__getConfluenceSpaces` with `cloudId: mozilla-hub.atlassian.net`).

You should see "Firefox Product Space" (key `FPS`, id `12484637`) in the response.

### Troubleshooting

- **`mcp__atlassian__*` tools missing after install**: run `/reload-plugins`. If still missing, check `/plugin` → Errors tab.
- **OAuth fails**: confirm you have permission on `mozilla-hub.atlassian.net`. The marketplace plugin's docs (linked from `/plugin` → Discover → atlassian) cover re-auth.
- **MCP call blocked by the auto-mode classifier**: this is a Claude Code permission prompt, not an MCP failure. Approve the call to proceed.

## Atlassian API token (legacy)

Only needed if you're falling back to the Python scripts in `scripts/`. The MCP path above is preferred.

**Email**: your Mozilla email address (e.g. `you@mozilla.com`)

**API Token**:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click **Create API token**
3. Enter a label (e.g. "train-hop") and copy the token

Export as `ATLASSIAN_EMAIL`, `ATLASSIAN_API_TOKEN`, and `ATLASSIAN_NAME` (your Feature Owner display name). As with the Bugzilla key, an untracked `.mozconfig-env` file at the repo root works well.
