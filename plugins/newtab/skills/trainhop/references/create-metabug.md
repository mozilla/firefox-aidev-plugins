# Train-hop: Create Meta Bug

Files the Bugzilla meta bug that tracks the full train-hop release. All other bugs filed during the train-hop process block this meta bug.

## Steps

### 1. File the meta bug

Use the `TARGET_VERSION` (the release-target version) determined by the orchestrator — see SKILL.md → "Determine the train-hop target version". If running this step standalone, default to `(Nightly major from browser/config/version.txt) − 2` and confirm with the user. Then run:

```bash
python3 <skill-scripts-dir>/file_bug.py \
  --summary "[meta] Firefox TARGET_VERSION train-hop metabug" \
  --type task \
  --keywords meta
```

The script prompts for your Bugzilla API key and prints the new bug ID. Note it — all subsequent bugs in this workflow will block it.

## Expected Result

The meta bug is visible at `https://bugzilla.mozilla.org/show_bug.cgi?id=BUG_ID` with summary `[meta] Firefox TARGET_VERSION train-hop metabug` and the `meta` keyword.

## Troubleshooting

**API returns an error**
The script prints the full message. Common cause: the `meta` keyword requires special Bugzilla permissions — ask a peer with those permissions to file it manually.
