---
name: backend-investigation
description: Diagnoses backend problems behind Firefox Home New Tab (HNT), across Merino, the curated corpus, admin-api, the article crawler, Picture of the Day and the daily crossword. Use when a Sentry alert fires on one of those services, an editor reports something broken, or a New Tab feature looks empty, wrong, or stale. Backend only, not in-tree browser/extensions/newtab frontend work.
---

# New Tab (HNT) Backend Investigation

Diagnose a problem in the backend services behind Firefox Home New Tab. The page is assembled from
features that are served separately and fail separately — content recommendations (Merino, the
curated corpus, admin-api, the article crawler, the ML section pipeline, the data pipelines),
Picture of the Day, the daily crossword — so establish which one the symptom belongs to before
probing. A New Tab feature with no notes in this skill is still yours to diagnose: work it the same
way, from the Merino provider and config that serve it. Not for in-tree `browser/extensions/newtab`
frontend bugs, and not for Merino's non-New-Tab consumers such as Firefox Suggest.

What you owe first is a **diagnosis**: a root cause, the evidence for it, and the impact quantified.
Mitigating or fixing the problem usually follows straight from that, so carry the diagnosis far enough
to name the change that would resolve it and what would show the recovery.

Two groups feel these failures, and every finding should say which one it reached: **Firefox New Tab
clients**, meaning everyone the affected feature serves, and, where the feature has them, the
**editors and curators** working through curation-admin-tools and admin-api.

Access and traps, per system: [references/data-sources.md](references/data-sources.md)

## How we like this done

You know how to investigate. These are the preferences that make an investigation here land well:

- **Confirm the symptom yourself before explaining it**, whatever the source reported.
- **Let the data generate the hypotheses**, one round at a time, rather than enumerating everything up
  front. Where several are live at once, probe them in parallel instead of serially.
- **Measure rather than reason.** Reproduce the request, count the rows, read the code path. The
  characteristic failure here is a correct query paired with a wrong inference, stated confidently.

## Don't stall on the developer

Every pause costs wall-clock, because the developer may not be watching. Default to proceeding:
pick the sensible option, say which one you picked, and keep going. Ask a blocking question only
when proceeding on any assumption would waste the whole investigation.

When a source you cannot reach looks promising, raise it **once** as a pending task carrying the
whole errand in its own text, prefixed `User action:` so it reads as theirs rather than yours — e.g.
`User action: connect to VPN so corpus MySQL is reachable — settles whether the DE items exist at
all`. Give the exact command, not a description of the problem; the "Access requests" section of
`references/data-sources.md` has the command for each gated source and how to word the ask. If the
answer lives in a dashboard or console you have no credential for, do not ask for access at all —
name the view, the filter, and the single number or shape you need, and ask them to read it back.

**Then keep investigating the other hypotheses immediately. Do not wait.**

Restate it exactly once more — whichever comes first: the unblocked lines run out, or you are three
probes into a line you had already judged weaker than the blocked one. That is the second and last
ask, and it does not apply if they have already answered. If there is still no response, write up and
close out with `Status: blocked`, name the one unblock under "Could not measure", and leave the access
task pending.

Stopping outright is a last resort: only when the blocked source is the only thing that can settle
the question **and** it cannot be reduced to a question they can answer for you — a dashboard,
console, or explore is almost never a real stop.

## Workspace

Each investigation gets its own subdirectory inside one root directory that the developer keeps their
investigations in. Do not assume where that root is. Establish it in this order:

1. **Check the instructions you were already given.** A root recorded on an earlier run is already in
   front of you, in your loaded instructions. If they name one, use it and do not ask.
2. **Otherwise ask, once, before your first write.** Where the developer keeps investigations cannot
   be derived, and guessing puts files somewhere they did not choose. Ask it as a single question at
   the start, and start pinning down the report while you wait rather than idling.
3. **Then remember it**, so the question is asked once per machine rather than once per investigation.
   Remember the root and the one-subdirectory-per-investigation convention, and say that you saved it.
   It has to persist for **every** repository, not only the one you happen to be in: investigations get
   started from whichever service repo is to hand.

Then create this investigation's subdirectory inside that root. If the root already holds
investigations, follow the naming they use; otherwise `<mon><DD>-<slug>`, e.g.
`jul29-empty-de-sections`. Say which directory you created. Reuse an existing one only when its
FINDINGS.md is about the same symptom.

- `FINDINGS.md` — one living document, from the skeleton in the write-up step. Create it once the
  directory exists and in any case before you write a conclusion down; the steps that follow write into
  it as they go, so the write-up step is a final pass over a document that already exists. Rewrite it in
  place, not as `FINDINGS-v2.md`.
- `HYPOTHESES.md` — the working list, live and dead, each with what would kill it. Hypotheses go here
  rather than in FINDINGS.md, which carries the conclusion they led to.
- Add subdirectories only when you have something to put in them, not up front: `queries/` and
  `results/` for each query and its output under a matching basename, `api_responses/` for raw JSON
  from live calls. Save responses even when they look boring; the same request may not return the same
  thing tomorrow.
- Aggregate before saving. This directory sits outside any repo and gets linked into tickets, so prefer
  a distribution over a dump of rows carrying editor identities or user data.
- Rewrite only the FINDINGS.md you wrote and delete only files this session created — anything else in
  the directory belongs to another investigation.
- Python work goes in an isolated venv inside this directory.

## Keep a timeline throughout

Maintain a `timestamp (UTC) | observation | source` table as you go rather than assembling one at the
end. Where the onset is cheap to establish, get it early: it constrains every other line of enquiry.
Where it is not, leave it open and say so. An assumed onset is worse than an unknown one, because
everything downstream quietly inherits it.

Normalise and label every timestamp, since a subtraction error can manufacture an outage that never
happened, and line the window up against the deploys and config changes you turned up.

**The scheduling layer is not in UTC.** Scheduled dates and the assembly crons run in each surface's
own timezone, so a UTC comparison invents a one-day gap for part of every day on any surface offset
from UTC — worst for the Americas, and `en-US` is the largest surface. Convert per surface, and say
which timezone you used.

## Step 1 — pin down the report

Before your first probe, read [references/data-sources.md](references/data-sources.md). It carries the
traps that silently return wrong answers, and several of them look like an outage.

Establish these five facts from the data.

| Fact | Why it matters |
|---|---|
| Exact symptom, verbatim, and which feature | "Empty section" and "wrong items in section" have disjoint causes |
| Who noticed, and how | Alert / editor report / spotted by hand — sets what evidence exists |
| First and last seen, **with timezone** | Anchors the timeline; reports usually arrive late |
| The stratum — surface, locale, section, client version, or for a daily artifact the date | The stratum is very often the diagnosis |
| Still happening right now? | Live reproduction vs. historical forensics |

If it is still happening, capture the perishable evidence first — a live request for the feature,
current logs, whatever counts or artifact it publishes — and establish what normal is while those
probes are in flight. History keeps; live signal does not.

**An error rate is not yet a symptom.** Measure the erroring stage's *output* to fix the blast radius:
items per section and per-surface freshness for assembly, the newest object under a dated prefix for a
publish job, a live Merino request for anything client-facing. An error floor that never reaches the
output is a not-incident; errors flat with output at zero is worse than the alert says.

**Failing to reproduce is a result, not a blocker.** Record the exact attempt, then switch the question
to why the reporter saw it and you do not: a stratum you did not hit, a closed window, a cache, a client
version, or a monitor measuring something other than what it claims. `not-incident` needs an answer to
that second question; unconfirmed is not refuted.

A report relayed from an editor is ambiguous between what editors see in curation-admin-tools and
what clients see on the surface. Probe both and state which group you confirmed. Once client-visible
impact is confirmed and still happening, say so in one line — what, how big, since when — and keep
going.

## Step 2 — establish what "normal" is

You have no idea what is currently normal here, so you have no basis on which to reject your own
inference. Derive the prior rather than asking for it:

- **What the serving path returns now** — a live request for the feature; for recommendations, the
  surfaces present and not disabled in the section data.
- **What the producer last wrote** — per-surface, per-source crawl volume over the last day for
  recommendations, the newest object under the dated bucket prefix for a publish job. Producer and
  serving sets differ, and a crawled surface with no sections is not automatically a bug.
- **What shipped recently** — commits in the service repos, releases in Sentry, timestamps on model or
  config artifacts.
- **Whether this is normally noisy or seasonal** — a trailing profile of the same metric, by day of
  week. Do not ask; compute it.
- **Whether it has happened before** — Sentry for the same signature, and the service repos' GitHub
  issues. Where one is unreachable, record it as unchecked rather than empty.

What is left is genuinely in the developer's head: anything in flight that a repo or dashboard would
not show, and whether a postmortem or incident register already covers this area. Raise that as one
short note and carry on without waiting.

Keep what you derived and what they told you apart in FINDINGS.md. When a later query contradicts the
prior, treat your own inference as the suspect first, and say so.

## Step 3 — form hypotheses from the data, then probe them in parallel

Start where pinning down the report left you: the stage whose output is wrong, the affected stratum,
the moment it changed. Ask what could produce exactly that, follow the data one hop upstream, and let
each result raise the next question.

Keep them in `HYPOTHESES.md`, a row each, and write the result that would kill one before you go
looking:

```markdown
| # | Hypothesis | What would kill it | Probe | Result | Status |
```

Status is live, killed, parked, or confirmed. Killed rows stay; they are what stops the next person
re-running them.

Work the live ones in parallel: issue the probes as parallel calls in a single batch, handing any line
that needs several dependent steps to a subagent. Keep the first wave small and quick, and hold
anything slow or wide for the second. Name each query file after its hypothesis so a result cannot be
attributed to the wrong line.

Then look at what came back, update the rows, and do it again. Being down to one surviving hypothesis
is a prompt, not an answer: ask what else could produce what you measured before committing to it. And when a source stops
yielding, measure the same thing in another plane — the failure is often invisible in the one you
started in.

## Step 4 — stratify before concluding anything

An aggregate that looks fine is the normal way these problems hide. Slice by the dimensions the feature
actually has — for recommendations **domain, locale, region, surface, section, experiment branch, and
client/addon version**, for a once-a-day global artifact barely more than the date — and look for a
single stratum at zero or down sharply against its own trailing median.
When the report says "some users" with no stratum attached, try experiment branch, region and rollout
state first: some surfaces are reachable only through enrolment, which a locale slice cannot see.

**Liveness is not health.** "The job ran successfully" is compatible with total data loss in every one
of these pipelines. Count what came out and compare it against what went in.

If the measurements exonerate the backend, stop at the service boundary: name the owning team and the
contract being broken, and hand it over. A second, unrelated anomaly you trip over on the way is a
one-line note plus a task, not a second investigation.

## Step 5 — try to break your own conclusion

Before writing anything down as fact, check the boring explanations: a filter in your own query, a
silent truncation, an unrepresentative code path, a column that does not mean what its name says, a
partially-launched feature. Then verify the outcome and not just the mechanism: a guard that provably
runs is not evidence that its effect is correct.

**Corroborate as widely as is reasonable.** Every source that can speak to the question is worth
reading, not merely a second one: one source agreeing with you is a hypothesis, and each further source
that could have failed differently and did not makes the claim harder to overturn. Do this even when the
first answer looked clear, because that is where a wrong inference survives. Stop when what is left
would only re-read the same plane, and record in FINDINGS.md which sources each claim rests on, so one
standing on a single source is visible as such.

**Contradictory results are the most valuable thing you can find, so do not smooth them away.** Weigh a
result the same whether or not it helps the hypothesis you favour: one that cuts against a hypothesis
already carrying evidence matters more, not less. Record it, say plainly what contradicts what, and make
the conflict the next question rather than something to be explained past.

The same holds when a measurement disagrees with the prior, or with what the developer told you is
working. Re-check the measurement first, since a stratum mismatch or a wrong surface identifier is
likelier than the system having changed under you. If it survives that, keep both on the record: say
which one you trust and why, tell the developer in one line, and carry on.

Mark every claim **verified**, **inferred**, or **refuted**, and keep the refuted ones.

## Step 6 — write FINDINGS.md

```markdown
# <feature>: <symptom> — investigation

**Status:** investigating | root cause identified | blocked
**Incident type:** outage | degradation | data-quality defect | user-facing bug | near-miss | not-incident
**Severity:** critical | high | medium | low — anchored to the magnitude below, not chosen by feel
**Affected:** Firefox clients | editors | both — with a magnitude, not an adjective

## Summary
Three sentences: what broke, since when, what the user-visible effect is.

## Timeline (UTC)
| Time | Observation | Source |

## Prior
**Derived** — what you measured, each with the query or link.
**Reported** — verbatim answers from the developer, or `asked <time UTC>, no answer received`.

## Evidence
Numbered findings. Each: the claim, the query or command, the result, and
verified/inferred/refuted. Reference saved files by path — every number reproducible from this
directory.

## Root cause
The mechanism, with the code path or config that produces it. "Not established" when it is not.

## Hypotheses
The surviving explanation, and the lines worth knowing were ruled out. `HYPOTHESES.md` alongside
has the full list with its kill conditions.

## Impact quantified
Rows, requests, users, hours, locales. A number, or an explicit "unquantified because X".

## Proposed fix
The change as a diff, at file-and-line where you can get there.

## Could not measure
Any telemetry plane you could not reach, and the access that would unblock it.
```

## Step 7 — close the loop

- **Leave unresolved access tasks on the list** rather than clearing them, and report what you could
  not reach as a finding rather than an inconvenience you routed around.
- **Link prior art** — older investigation, ticket, postmortem, or a related error already known.
- **Leave the follow-up as a task**, owned by whoever will act: confirm the fix shipped and the metric
  actually recovered. State that you have done so rather than asking whether to.
- Hand back a two-line verdict plus the FINDINGS.md path. Do not paste the document into chat.

### Posting to `#hnt-dev-be-alerts`

Updates worth sharing go to `#hnt-dev-be-alerts`. If the investigation started from an alert or message
posted there in the last day or two, find that one message and reply **in its thread**, so the
diagnosis stays attached to the alert people already saw. Otherwise start a new thread.

**Ask before every single message, showing the exact text and where it will go.** Approval for one
post is not approval for the next, and this is a shared channel colleagues act on. If approval does
not come, keep the draft in FINDINGS.md and carry on; an unposted update is not a reason to stop.
