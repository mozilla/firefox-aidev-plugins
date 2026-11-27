---
name: sccache-update
description: Bump the sccache version used by Firefox CI and measure its build-time impact on try. Use when asked to update, upgrade or bump sccache, or to compare build times/cache hit rates between two sccache versions.
---

# Updating sccache

We maintain sccache. We can modify and update this project if needed.

## 1. Bump the revision

sccache is fetched from git in `taskcluster/kinds/fetch/toolchains.yml`, entry
`sccache:`. Change the comment and the `revision:` to the release:

```yaml
        # 0.20.0 release
        revision: <sha>
```

Resolve the tag to the **commit** it points at, not the annotated tag object.
Use the `^{}` line:

```
git ls-remote https://github.com/mozilla/sccache 'refs/tags/v0.20.0*'
```

The toolchain tasks that build it are in `taskcluster/kinds/toolchain/sccache.yml`.
If the release raises its minimum Rust version, `linux64-rust-toolchain` may also
need a bump. A failing `TL(sccache)` task on try is the signal.

## 2. Commit and submit

Don't hesitate to propose to the developer to open a bug.

```
Bug NNNNNNN - Update sccache to X.Y.Z r?#firefox-build-system-reviewers
```

For review, submit like any other commits

## 3. Measure on try

Before pushing, read the release notes of every version between the old and
the new one (`https://api.github.com/repos/mozilla/sccache/releases/tags/vX.Y.Z`).
Look for changes to what is hashed: they change cache keys, so every build
misses until the cache refills. Also look for changes to the storage backends
(GCS, HTTP, DNS, auth), which affect the time of each hit.

To know beforehand whether a version will start with an empty cache, compare
`CACHE_VERSION` in `src/compiler/compiler.rs` between the tags:
`git grep -h 'const CACHE_VERSION' <tag> -- src`. Releases with the same
value share cache entries. The second `CACHE_VERSION` belongs to the
preprocessor cache (direct mode), which Firefox CI doesn't use.

Push the patched revision and its parent with **identical** task selections.
`mach try compare` is fzf-interactive only, so push twice by hand:

```sh
Q=(-q '^build-linux64/opt$' -q '^build-win64/opt$' -q '^build-macosx64/opt$' --rebuild 3)
./mach try fuzzy "${Q[@]}" -m "sccache X.Y.Z perf: NEW (bug NNNNNNN)" > artifacts/try-new.txt 2>&1
git checkout --detach HEAD^
./mach try fuzzy "${Q[@]}" -m "sccache X.Y.Z perf: BASE (bug NNNNNNN)" > artifacts/try-base.txt 2>&1
git checkout -   # back to the branch
```

When chaining checkouts and pushes in one shell command, check after each
`git checkout` that `HEAD` is the expected commit, and stop otherwise. Editors
and other tools run git commands in the background, and on a tree this size
`.git/index.lock` can stay held for several seconds. A failed checkout then
pushes whatever branch you were on, under the wrong label. Wait for the lock
to go away and retry, but never delete it: another git process may be
writing the index.

Check the selection first with `--no-push`. Each output file ends with a
Treeherder URL carrying a `landoCommitID`.

To measure another change on top, such as building sccache with PGO, push a
third revision with the same selection. Push only the commits being measured:
pushes contain every commit in the stack, and the decision task drops all tasks
when a commit message contains `DONTBUILD`, as skill commits often do. Put
the commits on a detached HEAD at the NEW revision:

```sh
git checkout --detach <NEW commit>
git cherry-pick <commits to measure>
./mach try fuzzy "${Q[@]}" -m "sccache X.Y.Z perf: PGO (bug NNNNNNN)" > artifacts/try-pgo.txt 2>&1
git checkout -
```

## 4. Collect the numbers

Lando queues try pushes, sometimes for several minutes. The job at
`https://lando.moz.tools/landing_jobs/<landoCommitID>/` stays `SUBMITTED` until
it reaches `LANDED` and its `commit_id` holds the try revision. Treeherder and the
Taskcluster index take a few more minutes to list the push. Use that revision
from then on: `treeherder-cli <landoCommitID>` can fail with `error decoding
response body` even after the job has landed.

```sh
curl -s https://lando.moz.tools/landing_jobs/<landoCommitID>/ | python3 -I -c \
  'import json,sys; d=json.load(sys.stdin); print(d["status"], d["commit_id"])'
treeherder-cli <rev> --filter '^build-' --watch
```

Every build task uploads `public/cidata/sccache-stats.json`, the output of
`sccache --show-stats` as JSON. It holds the sccache `version`, hits and misses
per language, cache read/write durations, the reasons requests weren't cacheable,
and error counters. Use it rather than scraping logs.
`scripts/compare_sccache_stats.py` (in this skill's base directory) finds every build task of both pushes,
including rebuilds, by listing the decision task's group. It fetches the
artifact for each one and prints per-task and per-label median tables, ready to
paste into a bug:

```sh
python3 -I <skill-dir>/scripts/compare_sccache_stats.py \
  base=<rev> new=<rev> [pgo=<rev> ...] > artifacts/sccache-compare.md
```

Deltas are against the first push. Tasks with a hit rate under 95% are left out
of the medians and counted in `runs` as kept/total. `--min-hit-rate` changes the
threshold.

`--filter <regex>` changes the task selection (default `^build-`). `--json`
dumps the raw rows. The per-label index routes
(`gecko.v2.try.revision.<rev>.firefox.<platform>`) keep only the latest task, so
don't use them to find rebuilds.

Read-hit and compile times are summed over all parallel compile jobs. They are
CPU-side totals, not wall clock. "Per hit" divides the read-hit time by the
number of hits. It includes the round trip to the cache bucket, so a gain in
sccache's own CPU time, such as the 3-5% upstream reports for PGO, is easily
lost in network noise. Only a large change in it is meaningful. Task duration
covers the whole task, including checkout and packaging.

## 5. Interpret

- The win64 and macOS builds are cross-compiled on Linux workers and run the
  `linux64-sccache` binary, like linux64. All three platforms measure the same
  sccache binary against different workloads, so a change to that one binary,
  such as PGO, shows on all of them.
- Check the `version` column first. Every NEW task must report the new
  version, otherwise the build didn't pick up the new toolchain.
- Compare per platform, on full-cache builds only. If the new version changes
  cache keys, every task that starts before one build has filled the cache
  misses. That includes all `--rebuild` copies and every other push using the
  same version (NEW and PGO, say), because they run at the same time. With
  only one or two full-cache runs left, push again once the cache is full,
  rather than drawing conclusions.
- Worker noise on try is usually ±5% on build time. Only report a difference
  larger than that, and only if all runs agree on its direction.
- Look at the "misses by compiler" column, not just the hit rate. A hit rate
  in the high 90s can hide one compiler missing heavily: sccache 0.19.0
  missed 46-223 Rust compilations per run with a 96-99% hit rate, and builds
  took three times as long. A version can change some keys without bumping
  `CACHE_VERSION`. `--rebuild` copies run at the same time, not one after
  another, so all of them miss together on a new key. That isn't proof of an
  unstable key.
- To see what missed and why, read `public/cidata/sccache.log` from the build
  task. It's at debug level: each compilation logs
  `[<crate or object>]: Hash key: <hex>`, then `Cache hit` or `Cache miss`.
  List the misses with:

  ```sh
  grep 'Cache miss in' sccache.log | grep -v conftest \
    | sed -E 's/^\[[^]]*\] \[([^]]+)\]: Cache miss.*/\1/' | sort | uniq -c
  ```

  Compare the `Hash key` of one missed crate across runs. The same key in
  every run means a cold cache. A key that differs between runs of the same
  revision means an unstable key. For Rust, the key covers the dependencies,
  so one crate with a new key makes everything that depends on it miss too:
  the earliest misses in the log are the root ones.
- Report the cold builds separately: their hit rate and duration show the
  one-off spike to expect once the change lands. Note that in the bug.
- "Per hit" is the wall time of `storage.get` in the sccache daemon,
  measured on its async runtime. It includes time waiting to be scheduled
  behind other work on that runtime, so it can rise while build durations
  don't move. Weigh it against durations before calling it a regression. DNS
  only matters for new connections: the daemon keeps one pooled HTTP client,
  so a build does about as many lookups as it has concurrent requests, not one
  per hit.
- A per-hit time difference measured while other pushes are filling the
  cache is not reliable. Confirm it with a second BASE and NEW push on a full
  cache before reporting it as a regression.
- Post a table in the bug: platform, BASE median, NEW median, delta, hit rates.

## 6. Test a patched sccache

To find which release introduced a change, bisect between releases first:
push the middle release (a `[try only]` commit setting `revision:` to its
tag's commit) together with BASE and NEW, on one platform with more
`--rebuild` runs. All three platforms run the same `linux64-sccache` binary,
so one platform with 6 runs gives a better median than three with 2.

To test whether one upstream change causes a difference, such as a revert or a
fix not yet released, build sccache from a branch in your GitHub fork of
mozilla/sccache:

1. Start the branch at the commit being measured, and apply the change. For a
   revert, `git revert <sha>` usually conflicts on `Cargo.lock`. Keep the
   release's lockfile (`git checkout --ours Cargo.lock`), then run
   `cargo metadata --format-version 1 > /dev/null`. That adds the missing
   crates without upgrading the others. Check that `git diff Cargo.lock`
   only adds packages.
2. Push the branch to the fork, and take the commit SHA from
   `git ls-remote https://github.com/<user>/sccache refs/heads/<branch>`.
3. On a detached HEAD at the NEW revision, point the `sccache:` fetch in
   `taskcluster/kinds/fetch/toolchains.yml` at the fork: set `repo:` to the
   fork's URL and `revision:` to that SHA. Commit it as
   `Bug NNNNNNN - [try only] ...` and push with the same task selection as the
   other runs. Never land that commit.
4. If the version string is unchanged, the build shares the cache keys of
   NEW, so it hits NEW's cache straight away. Compare it with NEW, both on a
   full cache.
