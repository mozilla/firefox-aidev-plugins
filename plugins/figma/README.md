# Firefox Figma Plugin

MCP server configuration for translating Figma designs into Firefox UI
code and for reviewing UX implementations against their Figma source.

## MCP Server

### `figma`

Connects to Figma's hosted remote MCP server at `https://mcp.figma.com/mcp`.

**First-run authentication:**

The first time the agent calls a Figma tool, Claude Code will open a
browser window and prompt you to sign in to Figma and grant access. The
OAuth token is cached locally — you won't be asked again until it
expires or is revoked.

No API key, personal access token, or Figma desktop app is required.

**What it exposes:**

Tools for reading Figma files the authenticated user has access to,
useful when implementing UX under `browser/`, `toolkit/`, or `mobile/`
from a Figma mockup, or when reviewing a patch against its design.
