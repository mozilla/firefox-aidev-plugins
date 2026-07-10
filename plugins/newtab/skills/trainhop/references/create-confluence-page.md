# Train-hop: Create Confluence Page

Creates the `HNT TARGET_VERSION Train Hop` tracking page in the FPS Confluence space.

This step is run **before** the QA ticket is filed (because the QA ticket needs the page URL). Once the QA ticket exists, this page is updated to swap the `QA-TBD` placeholder for the real ticket link.

## Constants

- **Cloud ID**: `mozilla-hub.atlassian.net` (the tools also accept the site URL directly; the UUID form is `d8febd08-c6e9-4c03-9c13-db37c2369ce5`)
- **FPS space ID**: `12484637`
- **Parent folder ID** ("HNT Train Hop Releases"): `1872035972`

> **Tool prefix:** tool names below are written `${MCP}<tool>`, where `${MCP}` is your Atlassian MCP prefix (`mcp__plugin_atlassian_atlassian__` for the official plugin). Resolve it once — see `references/credentials.md` → "Tool prefix (`${MCP}`)" — and substitute it into every `${MCP}...` name.

## Steps

### 1. Create the page

Use `${MCP}createConfluencePage` with **`contentFormat: "html"`**. This MCP documents and round-trips the HTML+ format most reliably; native dates (`<time>`), `@mention`s (`<span data-type="mention">`), inline cards, and code macros all render from HTML. (ADF is also accepted via `contentFormat: "adf"` but is less well documented here.)

**Required parameters**:

- `cloudId`: `mozilla-hub.atlassian.net`
- `spaceId`: `12484637`
- `parentId`: `1872035972`
- `title`: `HNT TARGET_VERSION Train Hop`
- `contentFormat`: `html`
- `body`: the HTML below, with placeholders substituted

### 2. Body template (HTML)

Substitute the placeholders (see below) before sending.

```html
<h3>Summary:</h3>
<ul>
<li>Meta Bug: <a href="METABUG_URL" data-card-appearance="inline">METABUG_URL</a></li>
<li>QA Bug: QA-TBD (will update once filed)</li>
<li>Timeline:
<ul>
<li>XPI Cut: <time datetime="XPI_CUT_DATE">XPI_CUT_DATE</time></li>
<li>QA Handoff: <time datetime="QA_HANDOFF_DATE">QA_HANDOFF_DATE</time></li>
<li>QA Sign-off: <time datetime="QA_SIGNOFF_DATE">QA_SIGNOFF_DATE</time></li>
<li>Release:
<ul>
<li>50%: <time datetime="RELEASE_50_DATE">RELEASE_50_DATE</time></li>
<li>100%: <time datetime="RELEASE_100_DATE">RELEASE_100_DATE</time></li>
</ul>
</li>
</ul>
</li>
<li>Rel Man contact: <span data-type="mention" data-user-id="RELMAN_ACCOUNT_ID">@RELMAN_NAME</span></li>
<li>QA contact: <span data-type="mention" data-user-id="QA_ACCOUNT_ID">@QA_NAME</span></li>
<li>Conductor: <span data-type="mention" data-user-id="CONDUCTOR_ACCOUNT_ID">@CONDUCTOR_NAME</span></li>
</ul>
<p>Release info:</p>
<p>Train hop Recipe:</p>
<pre><code class="language-json">{
  "addon_version": "",
  "xpi_download_path": ""
}</code></pre>
<h4>Helpful Links</h4>
<ul>
<li>See documentation: <a href="https://mozilla-hub.atlassian.net/wiki/spaces/FPS/pages/1785135275" data-card-appearance="inline">documentation</a></li>
<li>See check-list: <a href="https://mozilla-hub.atlassian.net/wiki/x/kABgag" data-card-appearance="inline">check-list</a></li>
<li><a href="https://sql.telemetry.mozilla.org/dashboard/new-tab-train-hop-add-on-uptake-dashboard">Real-time Train Hop Adoption Graph</a></li>
</ul>
<hr/>
<h3>Features being tested:</h3>
<p>These are the experiments/tickets that are planned as part of this release. They can be required or optional.</p>
<table><tbody>
<tr><th><strong>Jira Ticket / Summary</strong></th><th><strong>Product Owner</strong></th><th><strong>Priority</strong></th></tr>
<tr><td></td><td></td><td></td></tr>
</tbody></table>
<h3>QA Verified Bugs/Patches</h3>
<table><tbody>
<tr><th><strong>Bug</strong></th><th><strong>Summary</strong></th><th><strong>Landing Status</strong></th><th><strong>QA Status</strong></th></tr>
<tr><td></td><td></td><td></td><td></td></tr>
</tbody></table>
<h3>Shims added for <code>@backward-compat</code></h3>
<table><tbody>
<tr><th><strong>Bug Link</strong></th><th><strong>Title</strong></th><th><strong>Notes</strong></th></tr>
<tr><td></td><td></td><td></td></tr>
</tbody></table>
```

### 3. Placeholder substitutions

- `TARGET_VERSION` — Firefox release-target version (e.g. `152.0.5`)
- `METABUG_URL` — `https://bugzilla.mozilla.org/show_bug.cgi?id=BUG_ID`
- `*_DATE` — `YYYY-MM-DD`. Release is a **staged rollout**: `RELEASE_50_DATE` (50%) and `RELEASE_100_DATE` (100%, usually the next day). `<time datetime="YYYY-MM-DD">` renders as a native Confluence date.
- `RELMAN_ACCOUNT_ID` / `QA_ACCOUNT_ID` / `CONDUCTOR_ACCOUNT_ID` — Atlassian accountIds; resolve with `${MCP}lookupJiraAccountId`. Get the conductor's own id via `${MCP}atlassianUserInfo`.
- `*_NAME` — display name shown after `@`.

The **Train hop Recipe** JSON (`addon_version`, `xpi_download_path`) is left empty — the conductor fills it in manually after the recipe is generated.

Common accountIds (verify before use):
- Valentin Bandac (QA): `6310ac8255b0a9e29f1af16d`

### 4. Note the page ID and URL, and move it to the top

The response contains `id` and `_links.webui`. Pass them to the next step (file QA ticket).

### 5. Update the page after the QA ticket is filed

Once the QA ticket key is known, use `${MCP}updateConfluencePage` (pass the full HTML body again with the placeholder swapped). Replace the `QA Bug: QA-TBD ...` list item with:

```html
<li>QA Bug: <a href="https://mozilla-hub.atlassian.net/browse/QA-XXXX">QA-XXXX: Testing New Tab train-hop for Firefox TARGET_VERSION Release</a></li>
```

Pass `versionMessage: "Fill in QA ticket reference (QA-XXXX)"` so the page history is self-documenting.

## Expected Result

The page is accessible under "HNT Train Hop Releases" in the FPS space with the summary, timeline (interactive date macros, staged 50%/100% release), contact `@mention`s, and the empty Release info / Train hop Recipe block. The "Features being tested" / "QA Verified Bugs/Patches" / "Shims" tables are empty and filled in by the conductor.

## Troubleshooting

**MCP tools not found under the `${MCP}` prefix**
The plugin may register a different prefix. List available `mcp__*atlassian*` tools and use the matching names.

**MCP returns 404 on `parentId`**
The "HNT Train Hop Releases" folder may have moved. Search with `${MCP}searchConfluenceUsingCql` for `space = FPS AND title ~ "Train Hop"` and find the folder (type `folder`) — update the constant at the top of this file.

**HTML rejected with a validation error**
The MCP validates ADF nesting: list items can hold paragraphs, nested lists, and code blocks, but not headings/tables/panels; panels can't contain tables/expands. Read the returned error and adjust.

**Mention shows as `@unknown`**
The accountId is wrong. Resolve via `${MCP}lookupJiraAccountId` and try again.

**If the Atlassian MCP is unavailable**
Create the page manually in the Confluence UI: open the most recent `HNT … Train Hop` page, use **••• → Make a copy**, and update the title, dates, links, and @mentions.
