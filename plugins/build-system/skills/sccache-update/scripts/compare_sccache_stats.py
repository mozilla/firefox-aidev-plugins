#!/usr/bin/env python3
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""Compare sccache-stats.json and task durations between try pushes.

Each push is given as NAME=PUSH or PUSH, where PUSH is a Lando landing job ID
or a try revision. Deltas are relative to the first push.
"""

import argparse
import json
import re
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime

TC = "https://firefox-ci-tc.services.mozilla.com/api"
LANDO = "https://lando.moz.tools/landing_jobs/{}/"
STATS_ARTIFACT = "public/cidata/sccache-stats.json"


def get_json(url, attempts=5):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code < 500 or attempt == attempts - 1:
                raise
        except urllib.error.URLError:
            if attempt == attempts - 1:
                raise
        time.sleep(2**attempt)


def resolve_revision(push):
    if re.fullmatch(r"[0-9a-f]{12,40}", push):
        return push
    job = get_json(LANDO.format(push))
    if not job.get("commit_id"):
        sys.exit(f"Lando job {push} has not landed yet (status {job.get('status')})")
    return job["commit_id"]


def list_tasks(revision, name_re):
    decision = get_json(
        f"{TC}/index/v1/task/gecko.v2.try.revision.{revision}.taskgraph.decision"
    )["taskId"]
    url = f"{TC}/queue/v1/task-group/{decision}/list?limit=1000"
    token = None
    while True:
        d = get_json(url + (f"&continuationToken={token}" if token else ""))
        for t in d["tasks"]:
            if name_re.search(t["task"]["metadata"]["name"]):
                yield t
        token = d.get("continuationToken")
        if not token:
            return


def secs(d):
    return d["secs"] + d["nanos"] / 1e9


def parse_ts(ts):
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def collect(push, name_re):
    revision = resolve_revision(push)
    rows = []
    for t in list_tasks(revision, name_re):
        task_id = t["status"]["taskId"]
        runs = t["status"]["runs"]
        row = {
            "label": t["task"]["metadata"]["name"],
            "task_id": task_id,
            "state": t["status"]["state"],
        }
        if not runs or row["state"] != "completed":
            rows.append(row)
            continue
        run = runs[-1]
        row["duration"] = (
            parse_ts(run["resolved"]) - parse_ts(run["started"])
        ).total_seconds()
        try:
            data = get_json(
                f"{TC}/queue/v1/task/{task_id}/runs/{run['runId']}"
                f"/artifacts/{STATS_ARTIFACT}"
            )
        except urllib.error.HTTPError:
            rows.append(row)
            continue
        s = data["stats"]
        hits = sum(s["cache_hits"]["counts"].values())
        misses = sum(s["cache_misses"]["counts"].values())
        row.update(
            version=data.get("version"),
            requests=s["compile_requests"],
            hits=hits,
            misses=misses,
            miss_kinds=", ".join(
                f"{k} {v}" for k, v in sorted(s["cache_misses"]["adv_counts"].items())
            ),
            hit_rate=hits / (hits + misses) if hits + misses else None,
            not_cacheable=s["requests_not_cacheable"],
            cache_errors=s["cache_read_errors"]
            + s["cache_write_errors"]
            + s["cache_timeouts"],
            read_hit_s=secs(s["cache_read_hit_duration"]),
            read_per_hit_ms=secs(s["cache_read_hit_duration"]) / hits * 1000
            if hits
            else None,
            compile_s=secs(s["compiler_write_duration"]),
        )
        rows.append(row)
    return revision, rows


def median(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return statistics.median(vals) if vals else None


def fmt(v, kind):
    if v is None:
        return "-"
    if kind == "pct":
        return f"{v * 100:.1f}%"
    if kind == "s":
        return f"{v:.0f}s"
    if kind == "ms":
        return f"{v:.1f}ms"
    return str(v)


def delta(value, ref):
    return f"{(value - ref) / ref * 100:+.1f}%" if value and ref else "-"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("pushes", nargs="+", metavar="[NAME=]PUSH")
    p.add_argument("--filter", default=r"^build-", help="task name regex")
    p.add_argument("--json", action="store_true", help="dump raw per-task rows")
    p.add_argument(
        "--min-hit-rate",
        type=float,
        default=0.95,
        help="leave tasks below this hit rate (cold cache) out of the medians",
    )
    args = p.parse_args()
    if len(args.pushes) < 2:
        p.error("give at least two pushes")
    name_re = re.compile(args.filter)

    pushes = {}
    for i, spec in enumerate(args.pushes):
        name, _, push = spec.rpartition("=")
        rev, rows = collect(push, name_re)
        pushes[name or f"push{i}"] = {"revision": rev, "rows": rows}

    if args.json:
        json.dump(pushes, sys.stdout, indent=2)
        return

    print("## Pushes\n")
    for name, push in pushes.items():
        print(f"- {name}: {push['revision']}")

    print("\n## Per task\n")
    print(
        "| push | label | state | version | duration | hits | misses | hit rate "
        "| read-hit time | per hit | compile time | not cacheable | cache errors "
        "| misses by compiler |"
    )
    print("|" + "---|" * 14)
    for name, push in pushes.items():
        for r in sorted(push["rows"], key=lambda r: r["label"]):
            print(
                f"| {name} | {r['label']} | {r['state']} | {fmt(r.get('version'), '')} "
                f"| {fmt(r.get('duration'), 's')} | {fmt(r.get('hits'), '')} "
                f"| {fmt(r.get('misses'), '')} | {fmt(r.get('hit_rate'), 'pct')} "
                f"| {fmt(r.get('read_hit_s'), 's')} | {fmt(r.get('read_per_hit_ms'), 'ms')} "
                f"| {fmt(r.get('compile_s'), 's')} "
                f"| {fmt(r.get('not_cacheable'), '')} | {fmt(r.get('cache_errors'), '')} "
                f"| {r.get('miss_kinds') or '-'} |"
            )

    def warm(rows, label):
        return [
            r
            for r in rows
            if r["label"] == label and (r.get("hit_rate") or 0) >= args.min_hit_rate
        ]

    ref_name = next(iter(pushes))
    print(f"\n## Medians per label (deltas against {ref_name})\n")
    print(
        f"Only tasks with a hit rate of at least {args.min_hit_rate:.0%}; "
        "runs shows kept/total.\n"
    )
    print(
        "| label | push | runs | duration | delta | hit rate "
        "| read-hit per hit | delta |"
    )
    print("|" + "---|" * 8)
    labels = sorted({r["label"] for p in pushes.values() for r in p["rows"]})
    for label in labels:
        ref = warm(pushes[ref_name]["rows"], label)
        ref_d, ref_h = median(ref, "duration"), median(ref, "read_per_hit_ms")
        for name, push in pushes.items():
            total = sum(r["label"] == label for r in push["rows"])
            rows = warm(push["rows"], label)
            d, h = median(rows, "duration"), median(rows, "read_per_hit_ms")
            print(
                f"| {label} | {name} | {len(rows)}/{total} | {fmt(d, 's')} | {delta(d, ref_d)} "
                f"| {fmt(median(rows, 'hit_rate'), 'pct')} "
                f"| {fmt(h, 'ms')} | {delta(h, ref_h)} |"
            )


if __name__ == "__main__":
    main()
