#!/usr/bin/env python3
"""
Deletes stale runtime-metrics-N.json files from the New Tab metrics directory.

Reads the current Nightly major version from browser/config/version.txt and
removes any runtime-metrics-N.json file where N is less than that version,
as those files are no longer needed.

Must be run from the root of the Firefox source tree.
"""

import re
import sys
from pathlib import Path


def main():
    repo_root = Path.cwd()

    # Read current Nightly version to determine the cutoff
    version_path = repo_root / "browser/config/version.txt"
    if not version_path.exists():
        print(f"Error: {version_path} not found. Run from the Firefox repo root.", file=sys.stderr)
        sys.exit(1)

    version_text = version_path.read_text().strip()
    current_major = int(version_text.split(".")[0])

    metrics_dir = repo_root / "browser/extensions/newtab/webext-glue/metrics"
    if not metrics_dir.exists():
        print(f"Error: {metrics_dir} not found. Run from the Firefox repo root.", file=sys.stderr)
        sys.exit(1)

    deleted = []
    kept = []

    for f in sorted(metrics_dir.glob("runtime-metrics-*.json")):
        match = re.match(r"runtime-metrics-(\d+)\.json$", f.name)
        if not match:
            continue
        file_version = int(match.group(1))
        if file_version < current_major:
            f.unlink()
            deleted.append(f.name)
        else:
            kept.append(f.name)

    if deleted:
        print(f"Deleted ({len(deleted)}): {', '.join(deleted)}")
    else:
        print("No stale files to delete.")

    if kept:
        print(f"Kept ({len(kept)}): {', '.join(kept)}")


if __name__ == "__main__":
    main()
