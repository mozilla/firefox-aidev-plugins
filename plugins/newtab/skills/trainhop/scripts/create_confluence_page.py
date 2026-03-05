#!/usr/bin/env python3
"""
Creates the train-hop tracking page in the Firefox Product Space (FPS) Confluence space.

Prompts for Atlassian credentials at runtime.
Prints the URL of the created page on success.

Usage:
  python3 create_confluence_page.py \
    --version 147 \
    --metabug-url https://bugzilla.mozilla.org/show_bug.cgi?id=2008783 \
    --qa-ticket QA-4752 \
    --xpi-cut 2026-01-19 \
    --qa-handoff 2026-01-20 \
    --release-date 2026-01-22 \
    --relman "Ryan VanderMeulen" \
    --qa-contact "Valentin Bandac"
"""

import argparse
import base64
import getpass
import json
import sys
import urllib.request
import urllib.error

CONFLUENCE_BASE_URL = "https://mozilla-hub.atlassian.net/wiki"
SPACE_KEY = "FPS"
PARENT_PAGE_ID = "1872035972"  # "Train Hops" folder in FPS space
JIRA_BASE_URL = "https://mozilla-hub.atlassian.net/browse"


def get_auth_header(email, token):
    credentials = base64.b64encode(f"{email}:{token}".encode()).decode()
    return f"Basic {credentials}"


def build_page_content(args):
    qa_ticket_url = f"{JIRA_BASE_URL}/{args.qa_ticket}"

    return f"""<h3>Summary:</h3>
<ul>
  <li>Meta Bug: <a href="{args.metabug_url}">{args.metabug_url}</a></li>
  <li>QA Bug: <a href="{qa_ticket_url}">{args.qa_ticket}</a></li>
  <li>Timeline:
    <ul>
      <li>XPI Cut: {args.xpi_cut}</li>
      <li>QA Handoff: {args.qa_handoff}</li>
      <li>Release: {args.release_date}</li>
    </ul>
  </li>
  <li>Rel Man contact: {args.relman}</li>
  <li>QA contact: {args.qa_contact}</li>
</ul>
<h4>Helpful Links</h4>
<ul>
  <li><a href="https://mozilla-hub.atlassian.net/wiki/spaces/FPS/pages/1785135275">See documentation</a></li>
  <li><a href="https://mozilla-hub.atlassian.net/wiki/x/kABgag">See check-list</a></li>
  <li><a href="https://sql.telemetry.mozilla.org/dashboard/new-tab-train-hop-add-on-uptake-dashboard">Real-time Train Hop Adoption Graph</a></li>
</ul>
<hr/>
<h3>Features being tested:</h3>
<p>These are the experiments/tickets that are planned as part of this release. They can be required or optional.</p>
<table>
  <tbody>
    <tr>
      <th><strong>Jira Ticket / Summary</strong></th>
      <th><strong>Product Owner</strong></th>
      <th><strong>Priority</strong></th>
    </tr>
    <tr><td></td><td></td><td></td></tr>
    <tr><td></td><td></td><td></td></tr>
  </tbody>
</table>
<h3>QA Verified Bugs/Patches</h3>
<table>
  <tbody>
    <tr>
      <th><strong>Bug</strong></th>
      <th><strong>Summary</strong></th>
      <th><strong>Landing Status</strong></th>
      <th><strong>QA Status</strong></th>
    </tr>
    <tr><td></td><td></td><td></td><td></td></tr>
    <tr><td></td><td></td><td></td><td></td></tr>
  </tbody>
</table>
<h3>Shims added for <code>@backward-compat</code></h3>
<table>
  <tbody>
    <tr>
      <th><strong>Bug Link</strong></th>
      <th><strong>Title</strong></th>
      <th><strong>Notes</strong></th>
    </tr>
    <tr><td></td><td></td><td></td></tr>
    <tr><td></td><td></td><td></td></tr>
  </tbody>
</table>"""


def main():
    parser = argparse.ArgumentParser(description="Create the train-hop Confluence page")
    parser.add_argument("--version", required=True, help="Firefox major version (e.g. 147)")
    parser.add_argument("--metabug-url", required=True, help="Full Bugzilla metabug URL")
    parser.add_argument("--qa-ticket", required=True, help="Jira QA ticket key (e.g. QA-4752)")
    parser.add_argument("--xpi-cut", required=True, help="XPI cut date (e.g. 2026-01-19)")
    parser.add_argument("--qa-handoff", required=True, help="QA handoff date (e.g. 2026-01-20)")
    parser.add_argument("--release-date", required=True, help="Release date (e.g. 2026-01-22)")
    parser.add_argument("--relman", required=True, help="Release Management contact name")
    parser.add_argument("--qa-contact", required=True, help="QA contact name")
    args = parser.parse_args()

    email = input("Atlassian email: ")
    token = getpass.getpass("Atlassian API token: ")

    title = f"HNT {args.version} Train Hop"
    content = build_page_content(args)

    payload = {
        "type": "page",
        "title": title,
        "space": {"key": SPACE_KEY},
        "ancestors": [{"id": PARENT_PAGE_ID}],
        "body": {
            "storage": {
                "value": content,
                "representation": "storage",
            }
        },
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{CONFLUENCE_BASE_URL}/rest/api/content",
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
            page_id = result["id"]
            page_url = f"{CONFLUENCE_BASE_URL}/spaces/{SPACE_KEY}/pages/{page_id}/{title.replace(' ', '+')}"
            print(page_url)
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
