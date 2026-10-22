# Firefox Gecko Plugin

Skills for investigating Gecko bugs.

## Install

In the Firefox tree, the marketplace is already known, so run:

```
/plugin install gecko@firefox-aidev-plugins
```

Elsewhere, on Claude Code 2.1.275 or later:

```
/plugin install gecko --marketplace mozilla/firefox-aidev-plugins
```

## Skills

### `analyze-profile`

Analyzes a Firefox Profiler capture (a `share.firefox.dev` or
`profiler.firefox.com/public` link) with `profiler-cli` and writes a
structured findings report. The generic steps cover jank, long tasks, GC and
hot functions. Domain packs in `skills/analyze-profile/domains/` add the
threads and signatures of one subsystem; `media.md` is the first. See
[`skills/analyze-profile/SKILL.md`](skills/analyze-profile/SKILL.md).

## Optional tools

- [`profiler-cli`](https://www.npmjs.com/package/@firefox-devtools/profiler-cli)
  for `analyze-profile`.

## Adding domain knowledge

To add another subsystem or area, add a file to the skill's folder and a row for
it to the table in the skill's `SKILL.md`:

- `analyze-profile`: `domains/`, next to `domains/media.md`
