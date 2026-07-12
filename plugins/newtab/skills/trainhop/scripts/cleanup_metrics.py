#!/usr/bin/env python3
"""
Deletes stale runtime-metrics-N.json files from the New Tab metrics directory.

A train-hop generates fresh metrics files for the Beta (Nightly-1) and Release
(Nightly-2) channels. Any runtime-metrics-N.json for a version older than the
release channel is no longer needed and can be removed.

By default the release-channel version is derived from
browser/config/version.txt as (Nightly major - 2). Override with
--release-version if the train model ever differs. Files with N < release
version are deleted; N >= release version are kept.

Must be run from the root of the Firefox source tree.

Usage:
  python3 cleanup_metrics.py
  python3 cleanup_metrics.py --dry-run
  python3 cleanup_metrics.py --release-version 148
"""

import argparse
import re
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Delete stale New Tab runtime-metrics files")
    parser.add_argument(
        "--release-version",
        type=int,
        help="Release-channel major version (default: Nightly major from version.txt - 2)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be deleted without removing anything",
    )
    args = parser.parse_args()

    repo_root = Path.cwd()

    release_major = args.release_version
    if release_major is None:
        # Derive the release-channel version from the current Nightly version.
        # Firefox trains: Nightly = M, Beta = M-1, Release = M-2.
        version_path = repo_root / "browser/config/version.txt"
        if not version_path.exists():
            print(f"Error: {version_path} not found. Run from the Firefox repo root.", file=sys.stderr)
            sys.exit(1)
        version_text = version_path.read_text().strip()
        nightly_major = int(version_text.split(".")[0])
        release_major = nightly_major - 2

    metrics_dir = repo_root / "browser/extensions/newtab/webext-glue/metrics"
    if not metrics_dir.exists():
        print(f"Error: {metrics_dir} not found. Run from the Firefox repo root.", file=sys.stderr)
        sys.exit(1)

    print(f"Release channel version: {release_major} (keeping runtime-metrics-{release_major}.json and newer)")

    deleted = []
    kept = []

    for f in sorted(metrics_dir.glob("runtime-metrics-*.json")):
        match = re.match(r"runtime-metrics-(\d+)\.json$", f.name)
        if not match:
            continue
        file_version = int(match.group(1))
        if file_version < release_major:
            if not args.dry_run:
                f.unlink()
            deleted.append(f.name)
        else:
            kept.append(f.name)

    verb = "Would delete" if args.dry_run else "Deleted"
    if deleted:
        print(f"{verb} ({len(deleted)}): {', '.join(deleted)}")
    else:
        print("No stale files to delete.")

    if kept:
        print(f"Kept ({len(kept)}): {', '.join(kept)}")


if __name__ == "__main__":
    main()
