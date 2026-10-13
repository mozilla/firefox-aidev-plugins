# Credential Setup

Before running a train-hop you only need to set up **one** thing: a **Bugzilla API key**. Jira and Confluence sign you in automatically through the Atlassian plugin — no key to manage (see [Atlassian (Jira & Confluence)](#atlassian-jira--confluence) below).

## Set up your Bugzilla API key (one time)

**Full walkthrough:** https://mozilla-hub.atlassian.net/wiki/x/QoA4qg

In short: generate a key at https://bugzilla.mozilla.org (your name → **Preferences** → **API Keys**), then save it as a single non-empty line in `~/.mozbuild/trainhop.env`:

```
BUGZILLA_API_KEY=your_key_here
```

Do this in your own terminal or editor — **never paste the key into the Claude session** (chat or the `!` prefix), because anything typed there is saved in the conversation log. The train-hop only reads the file; it never asks for the key in-session. If the key is missing when a step runs, the skill points you to the doc above and stops.

### Notes (advanced)

- `~/.mozbuild` is Firefox's per-user directory — it already exists once you have a working local Firefox, keeps the key out of every repo, and survives plugin updates. `scripts/trainhop.env.example` is a template.
- An exported `BUGZILLA_API_KEY` overrides the file (handy for a one-off): `BUGZILLA_API_KEY=... python3 file_bug.py`.

## Atlassian (Jira & Confluence)

Jira and Confluence are handled by the **Atlassian MCP plugin** — you sign in once via OAuth and there's no API key to manage. It is published in the **official Anthropic marketplace** (`claude-plugins-official`), which is registered automatically when Claude Code starts. See the [Discover plugins → External integrations](https://code.claude.com/docs/en/discover-plugins#external-integrations) docs for the full list.

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

### Tool prefix (`${MCP}`)

Throughout this skill, **`${MCP}`** stands for the Atlassian MCP tool prefix. Resolve it once and substitute it into every `${MCP}<tool>` name (e.g. `${MCP}createJiraIssue`):

- **Official plugin** (the recommended install above): `mcp__plugin_atlassian_atlassian__`
- **Directly-configured MCP server** named `atlassian` (via `claude mcp add` / settings.json): `mcp__atlassian__`
- **Other / unsure**: list the available `mcp__*atlassian*` tools and use whatever prefix appears.

The tool *base names* — `createConfluencePage`, `createJiraIssue`, `updateConfluencePage`, `lookupJiraAccountId`, `atlassianUserInfo`, `getJiraIssue`, `searchConfluenceUsingCql` — are stable; only the prefix varies. A newly-added MCP server may only appear after `/reload-plugins` or a CLI restart.

### Verify

After install + reload, the `${MCP}*` tools should be available. A quick smoke test from Claude:

> List the spaces I can access in Confluence (use `${MCP}getConfluenceSpaces` with `cloudId: mozilla-hub.atlassian.net`).

You should see "Firefox Product Space" (key `FPS`, id `12484637`) in the response.

### Troubleshooting

- **`${MCP}*` tools missing after install**: run `/reload-plugins`. If still missing, check `/plugin` → Errors tab.
- **OAuth fails**: confirm you have permission on `mozilla-hub.atlassian.net`. The marketplace plugin's docs (linked from `/plugin` → Discover → atlassian) cover re-auth.
- **MCP call blocked by the auto-mode classifier**: this is a Claude Code permission prompt, not an MCP failure. Approve the call to proceed.
- **MCP entirely unavailable**: create the Jira ticket and Confluence page manually in the UI (clone a recent one) — see the "If the Atlassian MCP is unavailable" notes in `references/file-qa-ticket.md` and `references/create-confluence-page.md`.
