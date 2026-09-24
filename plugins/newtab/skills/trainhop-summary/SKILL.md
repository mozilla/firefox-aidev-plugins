---
name: trainhop-summary
description: Generate a categorized markdown changelog of commits between two newtab train-hop builds. Use when the user wants a release summary, train-hop changelog, or to summarize commits between two stations from the newtab-train-hop-station tool.
allowed-tools:
  - Bash
  - WebFetch
  - Read
  - Write
---

# Newtab Train-hop Summary

Generate a categorized markdown changelog of commits between two newtab train-hop builds.

## Data source

Stations are tracked in [`train-hops.yaml`](https://github.com/mikeconley/newtab-train-hop-station/blob/trainhop-data/train-hops.yaml) on the `trainhop-data` branch of [mikeconley/newtab-train-hop-station](https://mikeconley.github.io/newtab-train-hop-station/). Each entry:

```yaml
- version: 152.2.0.20260515.xxxxxx
  name: newtab-152.2.0-buildN
  git_sha: <40-char SHA in mozilla-firefox or autoland>
  mercurial_sha: <hg SHA>
  deployed_release_25: DD/MM/YYYY | N/A
  deployed_release_100: DD/MM/YYYY | N/A
  deployed_beta_100: DD/MM/YYYY | N/A
  notes: ...
```

Raw URL: `https://raw.githubusercontent.com/mikeconley/newtab-train-hop-station/trainhop-data/train-hops.yaml`

## Workflow

### Step 1 — Resolve the two endpoints

Always fetch the YAML first. Then:

1. **Default** to comparing the **last two listed** stations (newer at the bottom).
2. **Always confirm** with the user by listing the **5 most recent** stations as a numbered list with `name`, `version`, `git_sha[:12]`, and the latest non-N/A deployment date. Ask which pair to compare (e.g. "1 vs 4" → compare entry 4's SHA as base, entry 1's SHA as tip).
3. If the user passes two `git_sha`s directly in the invocation, skip the prompt.

### Step 2 — Verify SHAs exist locally

For each SHA: `git -C <firefox repo> cat-file -e <sha>`. If either is missing, tell the user to `git fetch` and stop. Do not proceed with a partial range.

### Step 3 — Pull commits

```
git -C <firefox repo> log --no-merges \
  --format='%H%n%an%n%s%n%b%n---COMMIT-END---' \
  <older-sha>..<newer-sha> \
  > artifacts/trainhop-<older-name>-<newer-name>.log
```

Per `AGENTS.md`, never pipe slow commands through `tail`/`grep`/`head` — write to a temp file under `artifacts/` (create it if needed) and read selectively.

### Step 4 — Resolve revert pairs

A commit whose subject starts with `Revert "..."` cancels the referenced commit. Track pairs and emit only the **net** set:

- Fully reverted, never relanded → drop entirely
- Reverted then relanded → keep once
- Ended in a reverted state → keep, but append `*(reverted — verify ship state)*` to the bullet

### Step 5 — Extract Bug + Phab IDs

- Subject: `Bug NNNNNNN - <title> r?...` (sometimes `Bug NNN, Bug MMM - ...` for multi-bug commits — split into one entry per bug)
- Body: `Differential Revision: https://phabricator.services.mozilla.com/DNNNNNN`

Hyperlink inline (per `feedback_bug_patch_hyperlinks`):

```
- [Bug NNNNNNN](https://bugzilla.mozilla.org/show_bug.cgi?id=NNNNNNN) — <title> ([DNNNNNN](https://phabricator.services.mozilla.com/DNNNNNN))
```

Multi-part bugs (e.g. `Bug 2034198 - Part 2`, `- Part 3`, `- Part 4`) collapse to one bullet with multiple Phab links.

### Step 6 — Categorize

Use these top-level buckets, in this order. Drop empty buckets.

**Per-widget sections** (one H2 per widget touched):

- Sports Widget
- World Clock Widget
- Lists Widget
- Weather Widget
- Timer Widget
- _any new widget that appears_

Identify by either the widget name in the subject or the touched directory (`browser/extensions/newtab/content-src/components/Widgets/<Name>/`). When ambiguous, run `git show --stat <sha>` to see which directory was touched.

**Cross-cutting buckets:**

- **Widgets Framework / Registry** — `WidgetsRegistry.mjs`, `Widgets.jsx`, shared context menu, widget infra
- **Nova (Design / Layout / Migration)** — design tokens (`--color-neutral-` → `--color-gray-`), CSS switcher, customization button, page layout
- **Sections / Stories / Cards** — DSCard, Billboard, MREC, topic selector, follow/block buttons, inline interest picker
- **Wallpapers**
- **Top Sites**
- **Preferences / Homepage** — `about:preferences#home`, `AboutPreferences.sys.mjs`, Customize panel
- **ASRouter Multistage Embed** — `asrouter-newtab-multistage`, `ExternalComponentWrapper`

**Meta / Low Tier** (always last, with these subsections in order):

- **Locales (train-hop)** — `Update locales for ...`, `Update newtab XPI locales`
- **Manifest / Version Bumps** — `Manually bump the minor version`
- **Train-hop Cleanup / Compat** — `Remove ... train-hop compatibility shims`, asset-folder additions for train-hop
- **Tooling / Build** — mach commands, pre-commit hooks, actor wiring, `remoteTypes`
- **Cross-cutting platform changes touching newtab** — anything where home-newtab-reviewers is a *secondary* reviewer on a non-newtab bug (e.g. searchfox redirects, `ownerGlobal` rename, modeline removal)

If a commit doesn't fit any bucket, put it under `Meta / Low Tier → Other`. Don't invent new top-level sections.

### Step 7 — Format the file

```markdown
# Newtab Train-hop: <older-name> → <newer-name>

<N> commits between <older-name> (`<older-sha[:12]>`) and <newer-name> (`<newer-sha[:12]>`).

## <Bucket name>
- [Bug NNNNNNN](...) — <title> ([DNNNNNN](...))
...

---

## Meta / Low Tier

### <Subsection>
- ...
```

Don't summarize commit titles further — the `Bug NNNN - <title>` shape is the canonical reference users want.

### Step 8 — Write the file

Path: `~/Desktop/Claude/newtab-trainhop-<older-name>-to-<newer-name>.md` (per `feedback_output_directory`).

Example filename: `newtab-trainhop-newtab-151.4.0-build1-to-newtab-152.2.0-build1.md`. Shorten by stripping the redundant `newtab-` prefix and `-buildN` suffix if it makes the name cleaner.

### Step 9 — Report back

Tell the user:
- Output path
- Total commit count (and net count after revert resolution)
- Any bugs flagged with `*(reverted — verify ship state)*`
- The pair of stations compared, with deployment dates

## Constraints

- Don't commit, stage, or push anything.
- Don't run `mach build` or any test commands — this skill is read-only against the Firefox checkout.
- The Firefox repo path is wherever the user has it (commonly `~/src/firefox`). If the current working directory isn't a Firefox checkout, ask the user for the path.
