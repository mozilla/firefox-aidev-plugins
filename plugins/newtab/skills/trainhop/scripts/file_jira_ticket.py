#!/usr/bin/env python3
"""
Creates a QA Jira ticket for a New Tab train-hop release.

Reads credentials from env vars ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN, and
ATLASSIAN_NAME (for Feature Owners), falling back to interactive prompts.
Prints the created ticket key (e.g. QA-1234) on success.

Usage:
  python3 file_jira_ticket.py --version 149 --meta-bug 2024043 \
    --confluence-url https://... --due-date 2026-01-22
"""

import argparse
import base64
import getpass
import json
import os
import sys
import urllib.request
import urllib.error

JIRA_BASE_URL = "https://mozilla-hub.atlassian.net"
PROJECT_KEY = "QA"
ISSUE_TYPE_ID = "11461"  # Functional
DEFAULT_LABELS = ["QA:Desktop", "QA:High"]

SHIPPING_METHOD = "System Add-on"
ENGINEERING_TEAM = "New Tab"
PRODUCT = "Desktop"


def get_auth_header(email, token):
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def main():
    parser = argparse.ArgumentParser(description="File a QA Jira ticket for a train-hop release")
    parser.add_argument("--version", required=True, help="Firefox major version (e.g. 149)")
    parser.add_argument("--meta-bug", required=True, type=int, help="Meta bug number (e.g. 2024043)")
    parser.add_argument("--confluence-url", required=True, help="Link to Technical Documentation (Confluence page URL)")
    parser.add_argument("--due-date", required=True, help="Due date in YYYY-MM-DD format")
    args = parser.parse_args()

    email = os.environ.get("ATLASSIAN_EMAIL") or input("Atlassian email: ")
    token = os.environ.get("ATLASSIAN_API_TOKEN") or getpass.getpass("Atlassian API token: ")
    owner_name = os.environ.get("ATLASSIAN_NAME") or input("Feature owner name: ")

    summary = f"Testing New Tab train-hop for Firefox {args.version} Release"
    description = (
        f"The New Tab team is performing a train-hop for Firefox {args.version}. "
        f"Please test the signed XPI on the Release channel using the staging "
        f"Experimenter rollout linked in the associated Confluence page."
    )
    meta_bug_url = f"https://bugzilla.mozilla.org/show_bug.cgi?id={args.meta_bug}"

    def adf_text(text):
        return {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": text}]}],
        }

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "issuetype": {"id": ISSUE_TYPE_ID},
            "summary": summary,
            "labels": DEFAULT_LABELS,
            "duedate": args.due_date,
            "description": adf_text(description),
            "customfield_10137": summary,
            "customfield_10138": owner_name,
            "customfield_10139": adf_text(args.confluence_url),
            "customfield_10151": {"value": SHIPPING_METHOD},
            "customfield_10140": adf_text(meta_bug_url),
            "customfield_10155": {"value": f"Fx{args.version}"},
            "customfield_10134": {"value": ENGINEERING_TEAM},
            "customfield_10147": [{"value": PRODUCT}],
            "customfield_10749": meta_bug_url,
        }
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{JIRA_BASE_URL}/rest/api/3/issue",
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": get_auth_header(email, token),
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            key = result["key"]
            print(f"{key}: {JIRA_BASE_URL}/browse/{key}")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error: HTTP {e.code} {e.reason}", file=sys.stderr)
        print(error_body, file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
