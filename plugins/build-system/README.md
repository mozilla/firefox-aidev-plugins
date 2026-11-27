# Firefox Build System Plugin

Skills for Firefox build system and CI toolchain work.

## Skills

### `sccache-update`

Bump the sccache version used by Firefox CI and measure its build-time impact
on try: where the revision lives, how to push comparable try runs, and a script
(`scripts/compare_sccache_stats.py`) that fetches the `sccache-stats.json`
artifact of every build task and prints per-task and per-label median tables
ready to paste into a bug. See
[`skills/sccache-update/SKILL.md`](skills/sccache-update/SKILL.md) for details.
