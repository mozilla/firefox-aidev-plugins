---
name: analyze-profile
description: Analyze a Firefox Profiler capture (share.firefox.dev or profiler.firefox.com/public links) for performance issues (jank, long tasks, hangs, high CPU, media playback), producing a structured findings report that other skills can consume. Triggers on "analyze profile", "analyze this profile", "/analyze-profile", or a Firefox Profiler URL.
argument-hint: <profiler-url>
allowed-tools: [Read, Bash(printenv GECKO_AGENT_MODE), Bash(profiler-cli *), Bash(searchfox-cli *)]
---

# /analyze-profile — Firefox Profiler Analysis

Analyze a Firefox Profiler capture for performance issues. Produces a
structured findings report that other skills can consume.

**Invocation**: `/analyze-profile <url>`

Where `<url>` is a `share.firefox.dev/*` or `profiler.firefox.com/public/*` link.

## Hackbot mode

Run `printenv GECKO_AGENT_MODE` before anything else. If it prints `hackbot`, you run unattended in the Hackbot cloud container, and these rules override the steps below. Otherwise skip this section: the skill runs as written.

- Never install or update a tool (`npm install`).
- Skip the code reading with `searchfox-cli`: it is not in the container. Name the function or marker that points at the code, so the caller can read it.
- If `profiler-cli` is too old for the profile, or it is the legacy CLI, report a tooling gap on our side and mark the analysis incomplete. It is not a question for the reporter.
- Instead of asking for a new capture (a `share.firefox.dev` link or a normal-mode profile): say in your answer which capture is necessary.
- Never ask a question or use AskUserQuestion: nobody is there to answer.

---

## ⚠️ Rules for callers

**All skills that encounter a Firefox Profiler URL MUST invoke this skill instead
of running `profiler-cli` directly.** Do not inline profiler-cli commands in any other skill. This skill is the single source of truth for profile
analysis.

Do NOT use `WebFetch` on profiler URLs — they are JavaScript SPAs; WebFetch returns
only the CSS shell with no profile data.

---

## Shell commands

This skill runs only `printenv GECKO_AGENT_MODE`, `profiler-cli` and `searchfox-cli`.
Use the Read tool for files. Run each command as its own Bash call, with literal values: do not
join commands with `;`, `&&` or `|`, do not set shell variables, and do not `cd`. The
only joined command is the stop check in the checklist below. Any other joined
command does not match the skill's `allowed-tools` rules, so it needs approval.

---

## ⚠️ Session cleanup checklist (REQUIRED)

Each `profiler-cli load` starts a background daemon that holds the whole profile in
memory (often 1–2 GB). It never exits on its own, so a run that does not stop it
leaks that memory until the machine restarts. Follow every item, on every run:

1. **Name the session before you load.** Pick `<id>` as Step 1 describes, and use only
   that id for the whole run.
2. **Pass `--session <id>` on every command.** Never rely on the current session.
3. **Stop it on every exit path**, not only at the end:
   - after the queries (end of Step 3),
   - after a failed load, if the load started the session. Never stop an id that `load`
     said is already running: another run owns it,
   - when the analysis is blocked or you give up,
   - before you report any error.
4. **Verify the stop.** Always stop with this command, which also checks the result:
   ```bash
   profiler-cli stop --session <id>; profiler-cli session list | grep -F -- "<id>" && echo "STILL RUNNING: <id>"
   ```
   If it prints `STILL RUNNING`, run it again. If the session is still listed, say so in
   the report.
5. **Report it.** The report must have the line `Session: <id> stopped`. A report
   without it is incomplete.
6. **Stop only your own session.** Never run `profiler-cli stop --all`, and never stop
   a session id that you did not create.

---

## Step 1 — Load the profile, then run the standard query set

`profiler-cli` must be on your `PATH`. If it is missing, ask the user to run
`npm install -g @firefox-devtools/profiler-cli`.

**Command shape (verified against profiler-cli 0.10.0).** It is a **subcommand** CLI and
is *stateful*: you `load` once to create a session, then query that session. The old
single-shot forms `profiler-cli <url> --calltree N`, `--top-markers N` and
`--log-markers` **no longer exist** and will fail.

Name the session yourself, so a leaked one can be traced in `profiler-cli session list`:
`<id>` is `ap-<bug>-<token>-<n>`, where `<bug>` is the caller's bug number (omit it and
its dash when there is none), `<token>` is the path segment after `share.firefox.dev/` or
the first 12 characters of the hash after `profiler.firefox.com/public/`, and `<n>` is a
number. Run `profiler-cli session list` first, and use the smallest `<n>` from 1 that no
listed session with the same `ap-<bug>-<token>-` prefix uses. Do not invent random
digits: they repeat across runs. If `load` still says the id is already running,
another run took it at the same time, so use the next number.

```bash
profiler-cli load <url> --session <id>
```

Then pass `--session <id>` on **every** subsequent command:

```bash
profiler-cli profile info --all      --session <id>                    # threads + CPU per process
profiler-cli thread list             --session <id>                    # every thread's t-N handle
profiler-cli thread functions        --session <id> --thread t-N --min-self 2
profiler-cli thread samples-top-down --session <id> --thread t-N       # where CPU goes
profiler-cli thread samples-bottom-up --session <id> --thread t-N --search <fn>
profiler-cli thread markers          --session <id> --thread t-N --limit 20
profiler-cli thread markers          --session <id> --thread t-N --search "<term>"
profiler-cli marker info             --session <id> m-NNNN             # one marker in detail
```

`--session` is **mandatory in practice**: the "current session" pointer is global and
not sticky, so any other concurrent `load` silently steals it and your queries start
describing someone else's profile with no error. Never run `profiler-cli stop --all`;
it kills other agents' sessions too.

**You own this session and must stop it.** Follow the session cleanup checklist above:
stop and verify as soon as the queries are done (end of Step 3), and on every early
exit.

**If the load fails, that is blocking — fix it and retry.** A profile is the artifact the
whole analysis rests on, so a failed read is never a caveat to note and move past:

| Failure                                                                          | Action                                                                                                                                                                            |
|----------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `This profile is version N, but this profiler-cli only supports up to version M` | The tool is stale. `npm install -g @firefox-devtools/profiler-cli@latest`, then retry.                                                                                            |
| `Unable to extract profile URL`                                                  | The link is a `profiler.firefox.com/from-browser/...` local-session URL and contains **no profile data**. Ask for a `share.firefox.dev` URL produced by **Upload Local Profile**. |
| `Please specify one of: --calltree <N>, …`                                       | The legacy git-clone `profiler-cli` is still installed under the same name. Run `npm install -g @firefox-devtools/profiler-cli@latest` to replace it, then retry.                 |

Only after upgrading and retrying may you report a profile as unreadable, and then you
must say so explicitly and mark the analysis incomplete rather than presenting a
conclusion drawn around the hole.

**The view can start zoomed.** A shared link can open on a selected range. The header
of each command shows `View:`, and a marker list says `(of N in the full range)`. If
the evidence you need can be outside the range, run
`profiler-cli zoom clear --session <id>` to see the whole profile.

**Check how the profile was captured before drawing regression conclusions.** A
**safe-mode** capture forces software compositing and software decode, so it looks
pathological on every build and cannot isolate a regression. If the reporter says the
symptom also appears in safe mode on the last-good version, their safe-mode profile
describes the safe-mode baseline, not the bug: say so and ask for a normal-mode capture.

---

## Step 2 — Start where the symptom is, then follow the evidence

**First, pick the domain pack.** The `domains/` directory next to this file holds the
threads, marker searches and signatures of one subsystem. If the symptom or the
threads in `profile info --all` match a pack in the table below, read it now, before
you look at any thread. A matching pack is **required**, not a hint.

**Then start with these threads:**

1. The `GeckoMain` thread of the process that shows the symptom: the content process
   for a problem in a page, the parent process for a problem in the browser UI.
2. Every thread class that the matching pack lists, in every process that has one.
3. The threads that use the most CPU in `profile info --all`. The busiest thread is
   often a result of the problem, not its cause, so do not settle on a cause from CPU
   use alone.

Run the pack's marker searches where the pack says, and check its signatures in
Step 3. Name the searches you ran in the report.

**Then follow the evidence.** Check another thread only when the profile leads you to
it: a hot stack waits on it, a marker names it, or an IPC message goes to its process.
When a marker or a stack points at a code path, read that code with `searchfox-cli`
to confirm the cause, instead of stopping at the symptom.
**Never stop at the first thread.** A symptom often spans more than one thread and
more than one process, so check every thread that the evidence reaches before you
conclude.

The packs:

| Pack                                   | Read it when                                                                                          |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|
| [`domains/media.md`](domains/media.md) | Media playback: `<video>`, `<audio>`, MSE, EME, WebAudio, WebRTC, or `Media*` and `AudioSink` threads |

If no pack matches, use only the generic steps.

---

## Step 3 — Pattern match against known signatures

After collecting raw output, check for these generic patterns, then for the signatures
in the domain pack from Step 2:

### Main-thread jank or long task
- Signal: `Jank` or `LongTask` markers on a `GeckoMain` thread:
  `thread markers --session <id> --thread <GeckoMain t-N> --min-duration 50`
- Confirm: zoom into the marker (`profiler-cli zoom push m-N --session <id>`), run
  `thread samples-top-down` to see which function holds the thread, then run
  `profiler-cli zoom pop --session <id>`. The zoom stays on until you pop it, and every
  later query covers only the zoomed range
- Meaning: the thread is blocked; input, painting and timers wait for it

### IPC / GC stall on main thread
- Signal: long-duration markers (`> 50ms`) on `GeckoMain`:
  `thread markers --session <id> --thread <GeckoMain t-N> --min-duration 50`, and
  `--category GC` for `GCMajor`, `GCSlice`, `GCMinor` and `CCSlice` markers
- Meaning: main thread blocked; can delay painting, input and media clock ticks, and
  cause A/V desync

### Hot function
- Signal: one function with a high self time in `thread functions --min-self 2`, or one
  branch with most of the total in `thread samples-top-down`
- Meaning: the CPU cost is in that code path; name the function and its caller chain
- Confirm: read the function with `searchfox-cli --define '<function>'` to see why it
  is slow

### Stop the session
No later step queries the profile, so stop the daemon now, before writing the report,
and verify that it is gone (checklist item 4):
```bash
profiler-cli stop --session <id>; profiler-cli session list | grep -F -- "<id>" && echo "STILL RUNNING: <id>"
```

---

## Step 4 — Produce structured findings report

Output the report in this format so callers can consume it directly:

```
─── Profile Analysis: <url> ──────────────────────────────────────
Threads checked: <every thread from Step 2, e.g. GeckoMain (content), GeckoMain (parent)>
Domain pack:     <pack name and the marker searches you ran, or none>
Session:         <id> stopped

Findings:
  ✓ <pattern name>: <what was observed, frequency, thread>
  ✗ <pattern name>: not detected
  …

Key log entries:
  [t=Xms] <ThreadName>: <message>
  …

Errors:
  [t=Xms] <ThreadName>: <NS_ERROR_* or HRESULT>
  …

Assessment:
  Severity:   [Critical / High / Medium / Low / None]
  Root cause: [Identified / Suspected / Unknown]
  Summary:    <2-3 sentences: what the profile shows, what it means for the bug>
  Sufficient to start a fix? [Yes / No — reason]
──────────────────────────────────────────────────────────────────
```

**Sufficient to start a fix** means: the profile alone (possibly combined with existing
bug context) gives enough evidence to identify the root cause and start a fix,
without needing additional data from the reporter.

---

## Notes for callers

- Use `/analyze-profile <url>`, and drive `profiler-cli` directly only when this skill
  is unavailable or has failed.
- If profiler-cli fails, follow the Step 1 failure table: a stale tool is upgraded and
  retried. Only a profile that is genuinely gone (URL expired, local-session link) is
  noted as `Profile: inaccessible — <reason>`, and the analysis is then marked
  incomplete rather than concluded around the gap.
- Callers that drive `profiler-cli` directly own their session the same way: follow the
  session cleanup checklist.
