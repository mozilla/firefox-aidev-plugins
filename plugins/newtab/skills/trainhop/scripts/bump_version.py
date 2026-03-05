#!/usr/bin/env python3
"""
Computes and applies the next New Tab version for a train-hop release.

Reads the current version from browser/extensions/newtab/manifest.json and
the current Nightly version from browser/config/version.txt, then:
  - If the manifest MAJOR matches Nightly MAJOR: bumps MINOR, resets PATCH to 0
  - If Nightly MAJOR is higher: uses Nightly MAJOR, resets MINOR and PATCH to 0

Must be run from the root of the Firefox source tree.
"""

import json
import sys
from pathlib import Path


def main():
    repo_root = Path.cwd()

    # Read current manifest version
    manifest_path = repo_root / "browser/extensions/newtab/manifest.json"
    if not manifest_path.exists():
        print(f"Error: {manifest_path} not found. Run from the Firefox repo root.", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    current_version = manifest["version"]
    parts = current_version.split(".")
    if len(parts) != 3:
        print(f"Error: unexpected version format: {current_version}", file=sys.stderr)
        sys.exit(1)

    manifest_major, manifest_minor = int(parts[0]), int(parts[1])

    # Read current Nightly version
    version_path = repo_root / "browser/config/version.txt"
    if not version_path.exists():
        print(f"Error: {version_path} not found. Run from the Firefox repo root.", file=sys.stderr)
        sys.exit(1)

    version_text = version_path.read_text().strip()
    nightly_major = int(version_text.split(".")[0])

    # Compute new version
    if manifest_major == nightly_major:
        new_version = f"{manifest_major}.{manifest_minor + 1}.0"
    elif nightly_major > manifest_major:
        new_version = f"{nightly_major}.0.0"
    else:
        print(
            f"Error: manifest MAJOR ({manifest_major}) is ahead of Nightly ({nightly_major}). "
            "Something is wrong.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write new version
    manifest["version"] = new_version
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    print(f"{current_version} → {new_version}")


if __name__ == "__main__":
    main()
