#!/usr/bin/env python3
"""
Creates a QA Jira ticket for a New Tab train-hop release.

Prompts for Atlassian credentials at runtime.
Prints the created ticket key (e.g. QA-1234) on success.

Usage:
  python3 file_jira_ticket.py --version 147
"""

import argparse
import base64
import getpass
import json
import sys
import urllib.request
import urllib.error

JIRA_BASE_URL = "https://mozilla-hub.atlassian.net"
PROJECT_KEY = "QA"
ISSUE_TYPE_ID = "11461"  # Functional
DEFAULT_LABELS = ["QA:Desktop", "QA:High"]


def get_auth_header(email, token):
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def main():
    parser = argparse.ArgumentParser(description="File a QA Jira ticket for a train-hop release")
    parser.add_argument("--version", required=True, help="Firefox major version (e.g. 147)")
    args = parser.parse_args()

    email = input("Atlassian email: ")
    token = getpass.getpass("Atlassian API token: ")

    summary = f"Testing New Tab train-hop for Firefox {args.version} Release"
    description = (
        f"The New Tab team is performing a train-hop for Firefox {args.version}. "
        f"Please test the signed XPI on the Release channel using the staging "
        f"Experimenter rollout linked in the associated Confluence page."
    )

    payload = {
        "fields": {
            "project": {"key": PROJECT_KEY},
            "issuetype": {"id": ISSUE_TYPE_ID},
            "summary": summary,
            "labels": DEFAULT_LABELS,
            "description": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": description}],
                    }
                ],
            },
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
            print(result["key"])
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
