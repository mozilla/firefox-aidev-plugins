# New Tab (HNT) backend — where to look

Reference for the `backend-investigation` skill.

Write your own queries: this file gives you the shape of the data and the traps, not canned SQL.
Access varies by developer. Verify a source is reachable before building a plan around it, and if it
is not, follow "Don't stall on the developer" in SKILL.md — raise it once as a task and keep
investigating, rather than stopping or silently substituting a weaker source.

**Keep bulk out of your context.** Several of these sources answer a small question with a very large
payload, and a context spent on raw JSON is a context not spent on the investigation. Where the bulk
arrives through a CLI or `curl`, redirect it to a file in the investigation directory and read back only
the slice you need; a `bq query` or `gcloud logging read` written to disk stays out of context. Where it
arrives through an MCP tool there is nothing to redirect, so hand that retrieval to a general-purpose
subagent and keep only what it reports back. The ones that catch people out:

- The **Experimenter API** returns every experiment, around 15 MB, and filtering after the fact still
  leaves megabytes. Project to the slug and branch fields before it reaches you.
- The **GCS ranking blobs** run to a few MB each. Freshness is a question about object metadata, so
  list the object rather than reading it.
- **`gcloud logging read` has no default limit.** Always pass `--limit` and a narrow `--format`.
- A live **`curated-recommendations`** response is a couple of hundred KB for one surface. Save it, then
  inspect fields.
- **Sentry issue detail** carries full stacks, tags and contexts per event, and it is an MCP tool, so
  delegate the decomposition rather than pulling events one at a time.
- Even repo files bite: `merino/configs/default.toml` is ~57 KB and `merino/web/api_v1.py` ~32 KB, both
  named below as things to consult. Grep them for the block you want.

If you are editing this file later: it holds non-derivable access facts and traps that silently
produce wrong answers. Worked incidents, current issue ids, canned queries, and symptom-to-cause
lookups belong nowhere in this skill.

## Contents

- The features behind the page, and where to look for one this file does not name
- Sentry — projects and the traps in reading them
- Merino — live requests, deployed revision, GCP projects, ranking inputs, the serve-stale cache
- **Content recommendations** — the pipeline and repos, vocabulary, BigQuery, corpus MySQL, the
  editor plane, AWS, assembly cadence, experiment enrolment, Zyte
- **Picture of the Day** — the daily publish job, and the cache that serves yesterday or nothing
- **Crossword puzzle of the day** — the vendor mirror, and the two manifests that date it
- Slack — `#hnt-dev-be-alerts`, where updates get posted
- **Access requests** — the one-line ask for each gated source

## The features behind the page

New Tab is assembled from features that are served separately and fail separately, so place the
symptom in one before probing: content recommendations (`curated-recommendations`), Picture of the
Day (`rss/picture-of-the-day`), the daily crossword (`games/particle`). Those are the ones with
notes here, not the extent of what the page carries; most of this file is recommendations because
that feature has by far the most moving parts. For anything else, find its provider under
`merino/providers/`, its config block in `merino/configs/default.toml`, and read
`merino/web/api_v1.py` as the index of what Merino serves New Tab.

Every path in this file is relative to a service repo, and the repos are listed under Content
recommendations below. Check for a clone at the obvious spot only, `ls -d ~/<repo-name>`, and read
anything missing through `gh api` or `gh search code`, which needs no clone: for one or two files that
is faster than cloning anyway. Do not go scanning the filesystem for a checkout. If repeated source
reading is genuinely slowing the investigation, that is the point to raise a `User action:` task
asking where the repo lives or for a fresh clone.

## Sentry

Reachable through the Sentry MCP server (its tools are prefixed `mcp__sentry__`). Prefer the
event-search tool over issue-search when you need a volume breakdown by error message — issue search
alone will not decompose an umbrella fingerprint.

If no `mcp__sentry__` tools are present the server is not set up in this session; see Access requests
for the setup errand. Do not spend effort reaching Sentry any other way than through the MCP. Service
logs and the BigQuery log sink cover part of the same ground in the meantime.

The HNT services are in the **`mozilla`** organisation, prefixed `hnt-`; issue short-ids look like
`HNT-CRAWL-9`.

`hnt-crawl` · `hnt-metaflow` · `hnt-curated-corpus-api` · `hnt-admin-api` ·
`hnt-curation-admin-tools` · `hnt-section-manager-lambda` · `hnt-corpus-scheduler-lambda` ·
`hnt-prospect-api` · `hnt-prospect-translation-lambda` · `hnt-serverless-image-cache` ·
`hnt-braze-content-proxy` · `hnt-feature-flags`

Merino is separate: project `merino-py`, also in `mozilla`, and it takes every feature Merino serves,
so `hnt-` marks the corpus and crawl services rather than the whole page. Some older projects exist in
the `pocket` org; prefer the `hnt-` ones for anything current. Enumerate the current projects before relying on
this list — a project that does not resolve is a naming change, not evidence of zero errors.

Traps:

- **`first seen` is bounded by retention**, so it is not onset. Nearly every long-running issue
  reports a first-seen date at the edge of the retention window.
- Issue volume is dominated by long-standing error floors. Establish what was already there before
  attributing anything to today, and check whether a floor *changed* rather than whether it exists.
- Decompose an issue by error message before trusting its title or trending it.
- Absence of events is weak evidence: a process that dies at startup, a job that drops items while
  reporting success, a write path disabled by a config flag, and a service whose Sentry integration is
  misconfigured or disabled for that environment all emit nothing.

## Merino

Reproducing the client call is often the fastest confirmation of a client-visible symptom. Each
feature has its own endpoint, named in its section below. For recommendations:

```bash
curl -s https://merino.services.mozilla.com/api/v1/curated-recommendations \
  -H 'content-type: application/json' \
  -H 'User-Agent: Mozilla/5.0 (X11; Linux x86_64; rv:153.0) Gecko/20100101 Firefox/153.0' \
  --data-raw '{"locale":"en-US","region":"US","topics":[],"sections":[],"feeds":["sections"],
               "enableInterestPicker":false,"inferredInterests":null,
               "experimentName":null,"experimentBranch":null}' \
  -o api_responses/merino-en-US.json
```

Nothing requires curl. Pick whatever suits the moment, and reach for a short script when you need to
vary a field across several requests or parse what comes back; either way send the body to a file.

`CuratedRecommendationsRequest` in `merino/curated_recommendations/protocol.py` is the authority on
that body. An out-of-range UTC offset is quietly coerced to null rather than rejected, so a malformed
one does not announce itself; the field is taken as either `utcOffset` or `utc_offset` and must be 0 to
23. `count` governs the flat list only and defaults to 100; it does nothing to the sections feed. Set
`experimentName` and `experimentBranch` to land on a branch.

Where the recommendations sit depends on what you asked for. With `feeds:["sections"]` the flat `data`
array comes back empty and the sections arrive under `feeds`, keyed by section id, each carrying its own
`recommendations`. Omit `feeds` and you get `data` instead. Worth checking either way: how many sections
came back, how many items each carries, presence of `followable` / `allowAds`, and the age of the newest
item.

`GET /__version__` returns the running commit and build URL. Use it before trusting a repo log:
a merged commit is not a deployed one, and a rollback is the change that most cleanly explains a
symptom that started or stopped on its own. The lambdas carry the same information as a `GIT_SHA`
environment variable.

Keep live calls to the ones you need. If you find yourself looping over locales or branches against
prod, query the telemetry instead. Stage answers payload-shape questions only — it reads prod corpus
data — and its host is internal-only, so a request from outside the network returns 404 rather than an
auth error: `https://stage.merino.nonprod.webservices.mozgcp.net`.

GCP projects, for log reads, metrics and GCS listings. Confirm these against the deployed values files
in the deployment repo rather than the in-repo TOMLs, which lag:

| Environment | Project |
|---|---|
| Merino prod | `moz-fx-merino-prod-5de4`; some buckets in `moz-fx-merino-prod-1c2f` |
| Merino stage | `moz-fx-merino-nonprod-db57` (deployed); `moz-fx-merino-nonprod-ee93` is legacy and still named in `stage.toml` |
| Crawl and ML | `moz-fx-mozsoc-ml-prod`, with gen2 Cloud Functions `prod-crawl-handler`, `prod-page-crawler`, `prod-ingester`, `prod-parser` |

When the logging API returns nothing useful, the BigQuery log sink for the same project usually does.
That sink table is far larger than anything in the BigQuery list below — check whether it has a
partition column and filter on it, aggregate inside the query rather than pulling rows, and
`--dry_run` first.

**Ranking inputs arrive as GCS blobs on a timer, and a stalled producer is invisible everywhere else.**
Merino pulls `engagement/latest.json` and `priors/latest.json` from its exports bucket on a short
interval and feeds them to the Thompson-sampling ranker (see `[default.curated_recommendations.gcs]`
in `merino/configs/default.toml`). If the producing Airflow DAG in `bigquery-etl` stops, Merino keeps
serving with frozen ranking: it logs at INFO, raises nothing, and no row in any table below changes.
Compare the blob's update time against the producing DAG's current `schedule_interval` rather than
against a remembered cadence.

**Merino serves stale on upstream failure, per pod.** When the corpus fetch fails and a warm cache
entry exists, it returns the stale entry *and* pushes the expiry out again, so the stale window has no
fixed bound while the upstream stays down. A corpus-api or client-api outage therefore reaches clients
as a successful 200 with old content, and only cold pods raise. One live request cannot refute an
upstream problem, and cannot establish its scope either.

## Content recommendations

Everything under this heading is recommendations-only: the crawl, the corpus, the editor plane and
the BigQuery tables have no counterpart for the other features, which are Merino plus a bucket. There
are no BigQuery or ETL tables for those, so do not go hunting for them.

### The recommendations pipeline, and which repo owns each stage

**crawl / discovery → hydration (Zyte) → curated corpus → ML section assembly → SQS →
corpus-scheduler / section-manager lambda → curated-corpus-api → client-api → Merino → Firefox New
Tab.** Editors act on the corpus through curation-admin-tools → admin-api → curated-corpus-api.
Telemetry lands in BigQuery.

`client-api` is the Apollo federated router (`Pocket/pocket-monorepo`, `servers/client-api`) and it
is easy to miss: it has **no Sentry project of its own in either organisation**, so a failure there
surfaces as a Merino symptom. Merino also reaches it at the **prod** endpoint unconditionally —
`CorpusApiGraphConfig.endpoint` returns `CORPUS_API_PROD_ENDPOINT` regardless of Merino's own
environment, and the dev constant beside it is unused — so stage Merino reads prod corpus data.

| Repo | GitHub | Role |
|---|---|---|
| `merino-py` | mozilla-services/merino-py | Serves every New Tab feature — recommendations, picture of the day, the crossword — plus Firefox Suggest |
| `content-monorepo` | Pocket/content-monorepo | Curated corpus, recommendations, section manager, the SQS lambdas |
| `content-ml-services` | mozilla/content-ml-services | Crawl, classification, section assembly (Metaflow, Cloud Functions) |
| `hnt-content` | mozilla/hnt-content | A rewrite of crawl and extraction. **In development, not serving production as of Aug 2026** — the crawl that runs is the one in `content-ml-services`, so a mechanism read out of this repo describes nothing that is live |
| `pocket-monorepo` | Pocket/pocket-monorepo | client-api federated router, shared infrastructure |
| `curation-admin-tools` | Pocket/curation-admin-tools | Editor-facing web app |
| `admin-api` | Pocket/admin-api | Federated GraphQL gateway for the admin tools |
| `bigquery-etl` | mozilla/bigquery-etl | New Tab engagement and Merino export ETL, and the Airflow DAGs behind it |
| `serverless-image-cache` | Pocket/serverless-image-cache | Thumbor image resize and cache |
| `firefox` | mozilla-firefox/firefox | Client side of the contract (`browser/extensions/newtab`) |

### Vocabulary: surface, locale, section, editorial section, assembly

A **surface** is one locale/market feed of the corpus, written `NEW_TAB_EN_US`. A **section** is a
topic row inside a surface. **Assembly** is the ML stage that decides which corpus items sit in which
section for a surface; it runs as Metaflow flows in `content-ml-services` and reaches the corpus
through SQS, and the stage is called several things across these repos, so pin down which one a claim
refers to.

An **editorial section**, called a **Custom Section** in the tooling, is one the editorial team creates
and maintains by hand, as against an **ML-managed** section that assembly produces and refreshes:
`createSource` / `updateSource` of `MANUAL` in corpus MySQL, against `ML`. So an empty editorial section
and an empty ML-managed section have disjoint causes, and establishing which kind you are looking at
comes before anything else. Editors manage them at
https://curation-admin-tools.readitlater.com/curated-corpus/custom-sections/, and one section is at
`.../custom-sections/<externalId>/<surface>/` — a link worth handing to the developer when the question
is what a section was meant to contain, since reaching it needs an editor session.

Merino's request `locale` is hyphenated (`en-US`) and the surface is **derived** from language plus
region by `get_recommendation_surface_id` in `merino/curated_recommendations/utils.py`, which also
branches on experiment enrolment — it is not a reformatting of the locale string. The `SurfaceId` enum
itself lives in `merino/curated_recommendations/corpus_backends/protocol.py`. Stratifying by locale and
stratifying by surface are therefore not the same slice, and some surfaces are reachable only through
enrolment. The quickest resolution is a live response: it echoes the surface it resolved to.

Merino rewrites item URLs with `utm_source=firefox-newtab-<surface-in-lower-kebab>` (`get_utm_source`
and `update_url_utm_source` in `curated_recommendations/corpus_backends/utils.py`), so a URL from a
response generally will not match a stored `url`. Do not reconstruct the parameter yourself: the
lookup covers only some surfaces, and where it has no entry the URL comes back unmodified. Trace items
by the stable id instead: the response's `corpusItemId` is the corpus GraphQL item `id`, which lines
up with `ApprovedItem.externalId` in corpus MySQL and `approved_corpus_item_external_id` in BigQuery.
Confirm that last hop on the first item you trace rather than assuming it.

### BigQuery

`bq` ships with the Google Cloud SDK and runs on your `gcloud` credentials, so a missing binary or an
unauthenticated session is the first thing to rule out, ahead of any dataset permission: `gcloud auth
list` shows whether there is an active account. The same credentials cover the `gcloud logging` and
GCS reads above. Confirm the billing project with a `--dry_run` before the first real query; try
`mozdata-nonprod` first, then a personal sandbox, usually `moz-fx-dev-<ldap>-sandbox`. Anything missing there is an access task, and
authenticating is interactive so it belongs to the developer.

Corpus, section and crawl state:

| Table | What it is for |
|---|---|
| `moz-fx-mozsoc-ml-prod.prod_rss_news.rss_feed_items` | Articles discovered by crawl — per-surface, per-source (`PAGE` vs `RSS`) volume over time |
| `moz-fx-mozsoc-ml-prod.prod_articles.zyte_cache` | Hydrated article metadata — what the pipeline believes an article says. Not unique per url; see the traps below before counting or joining it |
| `moz-fx-data-shared-prod.snowflake_migration_derived.sections_v1` | Section existence, enable/disable state, and surface, as an event stream |
| `moz-fx-data-shared-prod.snowflake_migration_derived.section_items_v1` | Which items sit in which section, and when each was last touched — the freshness check for a stalled section |
| `moz-fx-data-shared-prod.snowflake_migration_derived.corpus_items_current_v1` | One row per corpus item, deduped — but it keeps the latest row even when that row is a removal, so filter status yourself |
| `moz-fx-data-shared-prod.snowflake_migration_derived.scheduled_corpus_items` | Scheduled items; one row per item in practice. Nearly every market has moved from scheduled items to sections, so thin or absent scheduling is the migration rather than a fault — check whether the surface still schedules at all before reading anything into it |

Client-side telemetry, which is the only plane that answers "how many users" and the only one carrying
experiment branch or browser version:

| Table | What it is for |
|---|---|
| `moz-fx-data-shared-prod.telemetry_derived.newtab_visits_v1` | The experiment and browser-version stratum (`experiments`, `browser_version`, locale, country). Very large and `requirePartitionFilter` is on |
| `moz-fx-data-shared-prod.firefox_desktop.newtab_content_live` | The live plane, minutes behind rather than a day — the only one that can confirm a symptom that is happening now |
| `moz-fx-data-shared-prod.firefox_desktop_derived.newtab_content_items_daily_v1` | Daily item-level impressions and clicks. Carries no locale and no experiment branch, and its version column is null for most volume, so do not use it for those cuts |

The derived tables are T+1, so they cannot confirm a live symptom; reach for the live table when the
question is "is this happening right now". Confirm each object still exists before drawing a conclusion
from an empty result, and use `bq ls <dataset>` to settle whether something is a table or a view and
whether it is partitioned — a view has no partition column, so ordering a partition filter on one is a
query error.

These are the tables that come up most, not everything that is modelled. When they cannot answer the
question, `bigquery-etl` is the index of what else exists: each derived table has a directory at
`sql/<project>/<dataset>/<table>/` holding its `query.sql`, `schema.yaml` and `metadata.yaml`, so
grepping a table or column name there finds both what produces it and what sits beside it. If that repo
is cloned locally, hand the search to a subagent on the fastest model you have — it is a grep-and-read
job whose answer is a table name and a few columns, and delegating keeps a wide search out of your
context.

Traps that will silently give you a wrong answer:

- **`zyte_cache` is not unique on `canonical_url`** — some urls appear many times over — and
  `rss_feed_items` is not unique on it either. So the natural discovered-to-hydrated funnel join fans
  out several-fold and inflates every count in it. Dedupe **both** sides to one row per url before
  joining, and note that the event-log warning below is about a different set of tables — it does not
  make this one safe to count.
- **There is no domain column on `rss_feed_items`.** Derive the domain from `canonical_url` (or
  `origin_url` for the page it was found on). A per-domain funnel is a computed grouping, not a
  lookup.
- **`source` is null for everything crawled before 2025-08-11**, several million rows. A long
  per-source series will show `PAGE` and `RSS` springing into existence on that date; that is the
  column being introduced, not the crawl changing.
- **`crawled_date` and `published_date` are STRING; `crawled_at`, `published_at` and `loaded_at` are
  TIMESTAMP.** Use the timestamps for any time arithmetic.
- **A date filter does not narrow the big tables.** `rss_feed_items` (tens of GB) and `zyte_cache`
  (over a hundred GB) are **unpartitioned and unclustered**, so a date predicate scans the whole thing
  anyway; only naming fewer columns reduces it. Never `SELECT *` on them, and `--dry_run` first to see
  what a query will actually touch. The `snowflake_migration_derived` tables are day-partitioned on
  `happened_at` but do not require a partition filter, so supply one yourself.
- **The `*_v1` event tables are event logs, not current state.** Rows accumulate per change, so a
  plain `COUNT(*)` over-counts. Where you must reduce the log yourself, take the latest row per id and
  check the inflation ratio rather than assuming it.
- **`approved_corpus_items` is a filter, not a deduplication.** It excludes removed items but still
  carries multiple rows per item, so it is not a current-state view despite the name.
- **`sections_v1.source` is unusable for current sections** — null on about four fifths of all
  sections and on **every** currently-active one. Section ownership (`MANUAL` vs `ML`) comes from
  `Section.createSource` / `updateSource` / `deactivateSource` in corpus MySQL. A null `source` means
  unknown, never `MANUAL`.
- **Surface identifiers differ by table.** Crawl data uses `en_US`; section data uses
  `NEW_TAB_EN_US`. Joining or comparing them naively produces empty results that look like an outage.
- **Source mix varies by surface** — some have no RSS-sourced content, some no page-crawled content.
  Judge each surface against its own history.
- **Volume is strongly day-of-week seasonal.** Compare against a trailing median, never against
  yesterday.

### Curated corpus MySQL

Production database behind curated-corpus-api, reached through a preconfigured read-only login path.
Check what exists with `mysql_config_editor print --all`, and expect to need the AWS Client VPN — a hang
rather than an auth error is the usual symptom of being off it.

**Connect as a read-only user or not at all.** `pkt_curation_corpus` is the application's own account on
the prod cluster and carries full write and schema privileges; decline it even for a `SELECT`, and
decline it if it is the only credential on offer. Where no read-only account exists, that is a blocked
source: raise the request below and carry on with BigQuery, which answers most corpus questions anyway.

Check which account a login path actually holds before trusting it: `SELECT CURRENT_USER();` and
`SHOW GRANTS;`. The convention here is a personal account named for the developer, `<ldap>@%`, holding
`GRANT SELECT ON *.*` and `GRANT SHOW_ROUTINE ON *.*` and nothing that writes. If `CURRENT_USER()`
returns `pkt_curation_corpus`, or the grants include anything beyond reading, stop there and raise the
request below. Use `SHOW GRANTS` rather than `SHOW CREATE USER`, which prints the account's
authentication string.

Useful invocation guards: `--safe-updates` (caps returned rows at 1000 and aborts queries estimated
to examine over a million) and `SET SESSION max_execution_time=10000` (10s server-side cap). The
1000-row cap **truncates silently**, so add an explicit `LIMIT` or raise the cap when you need a
complete set. The million-row abort surfaces as `ERROR 1104`, and it is your own guard rather than
access or VPN — it fires on the first aggregate over `SectionItem`. Lift the examined-rows ceiling with
`SET SESSION sql_big_selects=1` or `--max-join-size`, which is a different control from the row cap.

Schema `curation_corpus`. The tables that matter: `ApprovedItem` (the corpus itself, keyed by
`externalId` and `url`), `SectionItem` and `Section` (placement and section config — `Section` also
carries `createSource` / `updateSource` / `deactivateSource`, the authoritative ML-vs-manual
ownership), `ScheduledItem` (surface scheduling, largely superseded by sections, and its `scheduledDate`
is a zoneless calendar date in the surface's own timezone), `RejectedCuratedCorpusItem`, and the `PublisherDomain` / `TrustedDomain` /
`ExcludedDomain` domain lists. `SectionItem` runs into the millions of rows and `ApprovedItem` into the
hundreds of thousands — check indexes with `SHOW INDEX` before filtering, since several obvious filter
columns are unindexed.

### The editor plane

When the symptom is editor-facing, reproducing it means an authenticated editor session, which is an
interactive login and therefore the developer's errand rather than yours. What you can do alone:
`hnt-admin-api` and `hnt-curated-corpus-api` in Sentry for the failure window, the corpus rows the
mutation would have touched, and the resolver itself in `Pocket/admin-api` and
`Pocket/content-monorepo`. That is usually enough to name the mechanism without a session.

### AWS

content-monorepo infrastructure runs in AWS. Discover profiles with
`grep -E '^\[profile' ~/.aws/config` and confirm one works with `sts get-caller-identity`; match prod
against dev to the environment you are investigating.

**The ML-to-corpus handoff is a queue, and it is where a day's candidates go missing quietly.** The
corpus-scheduler and section-manager lambdas are each fed by SQS with concurrency of one and a batch
size of one, and the shared construct gives each queue a dead-letter queue named after it. Check queue
depth, in-flight count, oldest-message age, and DLQ depth before concluding that ML produced nothing:
a backlog and a drained DLQ look identical in every corpus table. Two mechanics worth knowing: a
message whose handler outlives the queue's visibility timeout is redelivered while still in flight and
can exhaust its receive count without any error being raised, and the write path is gated by an
`ALLOWED_TO_SCHEDULE` flag that makes the lambda return normally while writing nothing. ML also has one
path that bypasses the queue and calls admin-api directly, so do not describe the handoff as
queue-only.

CloudWatch Logs Insights is frequently the source that cracks a case for these lambdas — it will give
you total operation counts and per-error-type breakdowns that Sentry structurally cannot, because
Sentry only sees what was raised. Pass a reasonably small `--start-time`/`--end-time` that could answer
the question, and `stats`-aggregate rather than dumping `fields`. Also useful: alarm history (transition timestamps and state-reason margins), and pulling an
anomaly band itself as a metric-math series to compare its predicted centre against reality. The crawl
runs in GCP, not AWS, so its equivalent plane is Cloud Logging or the BigQuery log sink.

SSO sessions expire and the login is interactive, so it has to be the developer: see the table below.

### Assembly and cadence

Freshness thresholds are a common thing to want and a common thing to invent. Derive the intended
cadence from the `@schedule` decorators on the Metaflow flows in `content-ml-services/jobs/metaflow/`,
and record the interval you used in FINDINGS.md. Some decorators also pass a per-surface timezone, so
that schedule is surface-local rather than UTC.

Which flows are deployed is per-locale, listed in `jobs/metaflow/deployed_flows_<locale>.json` in the
same repo. A surface whose flow is not deployed is a third possibility alongside a crawl gap and a
serving gap.

### Experiment enrolment

Stratifying makes experiment branch one of the first cuts, and the branch names are not in any of the
tables above. The Experimenter API lists live and recent experiments without authentication:
`https://experimenter.services.mozilla.com/api/v6/experiments/`. Use it to get the real slug and branch
names before slicing telemetry, rather than inventing them or asking. It returns every experiment, so
write it to a file and project out the slugs and branches there; see the context note at the top of
this file.

### Zyte

Two separate APIs, both talking to a third party. Save every response, and reproduce the one or two
URLs the question turns on rather than sweeping a domain. Check for a key with `[ -n "$ZYTE_API_KEY" ] && echo present`. Reference keys by
variable name in anything you save, so no value lands in a query file or the transcript.

**Extraction API** (`ZYTE_API_KEY`, created at https://app.zyte.com/o/612928/zyte-api/api-access)
reproduces what the crawler saw for a URL. Request `article` for a single page or `articleList` for an
index page — not both — and put `extractFrom: "httpResponseBody"` inside `articleOptions` /
`articleListOptions` to skip the browser. Check **`statusCode` and the extraction probability before
anything else**: a non-2xx, a bot wall, or a "JavaScript is disabled" page still returns a populated
object that reads like success. Probability lives at `article.metadata.probability` for a single page
and per item at `articleList.articles[].metadata.probability` — `articleList.metadata` carries only
`dateDownloaded`. Compare `canonicalUrl` against the URL you requested; cross-domain canonicals pull
unapproved domains into the corpus.

**Stats API** (`https://zyte-api-stats.zyte.com/api/stats`) is the vendor's own view of your traffic:
per-domain response-code distribution over time. It takes a **different credential** — the Zyte
dashboard API key from the organisation's settings page, explicitly not the Zyte API key above, held
here as `ZYTE_SECRET_KEY`.

Authentication is HTTP basic with that key as the **username and no password**, which is fiddlier than
it sounds and is the usual reason a request that looks right fails. With curl, `-u "$ZYTE_SECRET_KEY:"`
— **the trailing colon is required**, because without it curl reads the whole string as a username and
stalls waiting for a password. Constructing the header by hand works too, as
`Authorization: Basic <base64 of "<key>:">`, with the colon inside the encoded string. Read the status
code before anything else: `401` means no usable credential reached the server, and `403` means a valid
Zyte credential that is not the dashboard key, which in practice means the extraction key was used.

`organization_id` is **required** and is `612928`. Only `groupby_time` (`hour|day|month|year`) and
`groupby_domain` group; `response_codes`, `domains`, `extraction_type` and `extraction_from` are
*filters*, not groupings, and `include_domain_health=true` is rejected without `groupby_domain=true`.

Two defaults will quietly narrow an answer. **`start_time` defaults to seven days ago**, so a question
about when something began returns only the last week unless you pass an explicit window with
`end_time`. And results are **paginated, `page_size` maxing out at 500**, so a per-domain breakdown over
any real window is truncated unless you walk `page`. Both look like a complete answer.

This is the right source for "did this domain start failing, and when" — your own logs will not show it
if the pipeline discards non-allowlisted status codes.

## Picture of the Day

```bash
curl -s 'https://merino.services.mozilla.com/api/v1/rss/picture-of-the-day' -H 'Accept-Language: de-DE'
```

The response is localised to `Accept-Language` where a translation exists, so send the locale you are
investigating rather than the default. It serves only what the daily `wikimedia_potd_updater` job put
at `wikimedia_potd/<YYYY-MM-DD>/potd.json` in the images bucket, so today's object existing separates a
producer problem from a serving one; a failed run is one `merino-py` Sentry event, exit code 0. The
manifest is cached per pod against today's UTC date and a failed refresh keeps the old entry: pods
that cached yesterday serve yesterday's picture while pods started since return `null` — both HTTP
200, logged at info, raised nowhere, and counted only by `potd.provider.cached.none`.

## Crossword puzzle of the day — the `particle` provider

```bash
curl -s 'https://merino.services.mozilla.com/api/v1/games/particle'
```

It takes no parameters and returns a tiny payload, the public URL of a static site in a bucket, so a
healthy endpoint says nothing about today's puzzle. A cron (`games_tasks update-particle`) diffs the
vendor's `runtime-manifest.v1.json` against the bucket's copy by version, per channel — `daily` is the puzzle,
`runtime` the engine — never by date; both manifests are public, so fetch each to see which side is
behind. A run logs `Files updated? False` whether it was idle or failed and emits no metrics, so
Sentry is the rest of the plane; `docs/providers/games/particle.md` has the detail.

## Slack

`#hnt-dev-be-alerts` is where investigation updates go. Posting needs the developer's approval for
**each** message and prefers a reply in the thread of the alert that started this, so locating that
one message is what the `mcp__slack__` tools are for here; the rule is under "Posting to
`#hnt-dev-be-alerts`" in SKILL.md. See Access requests if the tools are absent.

## Access requests

Raise one of these when the source looks promising, then keep working. Give the command, not a
description of the problem.

**How to ask.** Put the errand on the todo list, one item per step, each prefixed `User action:` so it
reads as theirs rather than yours, with the whole instruction in the item text. The commands below run
in the developer's own shell, so say **"in a new terminal"** rather than expecting them to run inside
this session. Where the fix changes which tools Claude Code has — installing an MCP server, exporting
a key into the environment — the change only takes effect on a fresh start, so make the **last** item:

```
User action: restart Claude Code in this directory with `claude --continue`, which picks this
session back up where it left off
```

Then carry on. The items stay pending and visible while you work; close them when they land, and delete
any whose line stopped mattering.

Roughly ordered by how often an investigation needs them, and how quickly they are resolved.

| Blocked source | Ask them to |
|---|---|
| `gcloud` installed but not authenticated | `gcloud auth login`, plus `gcloud auth application-default login` if you need the Python client libraries |
| `gcloud` or `bq` not installed | Install the Google Cloud SDK, which provides both |
| No billing project configured | Confirm you can bill `mozdata-nonprod`, or name their personal sandbox, usually `moz-fx-dev-<ldap>-sandbox`; either can be set with `gcloud config set project <id>` |
| No `mcp__sentry__` tools at all | `claude mcp add --scope user --transport http sentry https://mcp.sentry.dev/mcp`, then `/mcp` in the restarted session to authenticate |
| Sentry connected but unauthenticated or scoped too narrowly | `/mcp`, and authenticate for the `mozilla` org |
| Corpus MySQL hangs rather than erroring, and they have the VPN client | Connect to the AWS Client VPN, then say so; if it still hangs, the login path itself is stale |
| Corpus MySQL hangs and there is no VPN client installed | Install the AWS VPN Client from https://aws.amazon.com/vpn/client-vpn-download/, then download the client configuration from the endpoint page — https://us-east-1.console.aws.amazon.com/vpcconsole/home?region=us-east-1#ClientVPNEndpointDetails:clientVpnEndpointId=cvpn-endpoint-0d3c4e4a0121a5763 — load that profile into the client, connect, and say so |
| AWS SSO session expired | `aws --profile <profile> sso login` |
| The answer is in a dashboard you cannot reach | Open it, apply the specific filter you name, and read back the one number or shape you asked for. Asking for *access* to a dashboard is usually the slower path; asking a precise question about what it shows is faster for both of you |
| No AWS profile at all | `aws configure sso` for a read-only role, or have them name a profile already in their `~/.aws/config` |
| No read-only MySQL account for them yet | Have someone with an admin credential create a personal one, matching the existing convention: `CREATE USER '<ldap>'@'%' IDENTIFIED BY '<password>';` then `GRANT SELECT ON *.* TO '<ldap>'@'%';` and `GRANT SHOW_ROUTINE ON *.* TO '<ldap>'@'%';` — nothing that writes |
| No MySQL login path configured | Store that account as a login path: `mysql_config_editor set --login-path=prod-curated-corpus-api-readonly --host=<host> --user=<ldap> --password`, and tell you the path name, not the password |
| Permission denied on a dataset or a Merino project | Request read access, or viewer on the project; say meanwhile whether the question is about payload shape, which stage can answer |
| No `mcp__slack__` tools | `/plugin install slack@claude-plugins-official` typed into Claude Code, then `/mcp` to authenticate. The server needs a fixed OAuth callback port, so it can clash with another session authenticating at the same moment. Or have them post the drafted message to `#hnt-dev-be-alerts` themselves |
| Zyte extraction key missing | Create one at https://app.zyte.com/o/612928/zyte-api/api-access, then add it to the `env` block of `~/.claude/settings.json`: `"env": { "ZYTE_API_KEY": "<key>" }`. That reaches every session and the commands it spawns, and it is the user-scope file rather than anything checked in. A shell `export` will not reach this session, which did not inherit it |
| Zyte Stats key missing | Get the **dashboard** API key from https://app.zyte.com/o/612928/settings, via the `Download your API key as .TXT` button — the extraction key will not authenticate against the Stats API — and add it to the same `env` block as `ZYTE_SECRET_KEY` |
| Editor-facing symptom needs an authenticated session | Reproduce the click themselves and report the exact error text and time |
