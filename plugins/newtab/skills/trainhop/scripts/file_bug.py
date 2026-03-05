#!/usr/bin/env python3
"""
Files a Bugzilla bug for a New Tab train-hop step.

Prompts for the Bugzilla API key at runtime.
Prints the new bug ID to stdout on success.

Usage:
  python3 file_bug.py --summary "Update locales for Firefox 147 train-hop"
  python3 file_bug.py --summary "..." --blocks 2008783
  python3 file_bug.py --summary "..." --keywords meta --type task
"""

import argparse
import getpass
import json
import sys
import urllib.error
import urllib.request


def main():
    parser = argparse.ArgumentParser(description="File a Bugzilla bug")
    parser.add_argument("--summary", required=True, help="Bug summary")
    parser.add_argument("--product", default="Firefox")
    parser.add_argument("--component", default="New Tab Page")
    parser.add_argument("--version", default="Trunk")
    parser.add_argument("--type", default="defect")
    parser.add_argument("--keywords", nargs="*", default=[], help="Bug keywords (e.g. meta)")
    parser.add_argument("--blocks", type=int, help="Bug number that this bug blocks")
    args = parser.parse_args()

    api_key = getpass.getpass("Bugzilla API key: ")

    payload = {
        "api_key": api_key,
        "product": args.product,
        "component": args.component,
        "summary": args.summary,
        "version": args.version,
        "op_sys": "All",
        "platform": "All",
        "type": args.type,
    }

    if args.keywords:
        payload["keywords"] = args.keywords

    if args.blocks:
        payload["blocks"] = [args.blocks]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://bugzilla.mozilla.org/rest/bug",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            print(result["id"])
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error: HTTP {e.code} {e.reason}", file=sys.stderr)
        try:
            error_json = json.loads(error_body)
            print(f"  {error_json.get('message', error_body)}", file=sys.stderr)
        except json.JSONDecodeError:
            print(f"  {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
