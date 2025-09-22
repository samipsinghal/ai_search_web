Web Crawler — Technical Design Document 
Doc Status: Draft v1.0
Owners: Samip Singhal (ENG), TAs (review)
Reviewers: Course staff, peers
Last Updated: 21 Sep 2025
Code Link: crawler/ repo (Python 3.10+)
Related: HW1 handout; Lecture 1–2 notes; Manning IR text; Suel & Shkapenyuk crawler paper; ACHE focused crawler
0. TL;DR
We are building a single‑node, breadth‑biased, polite web crawler to collect HTML pages for later indexing (HW2). It prioritizes domain coverage, enforces robots.txt and per‑host politeness, ignores PDF bodies while harvesting any http(s) links found in them, and provides first‑class observability. The crawler targets 10,000 unique registrable domains in the first pass and a local benchmark of ≥50 pages/sec.
1. Problem & Context (Why)
Search engines rely on crawlers that scale, respect site policies, and produce high‑quality logs. HW1 requires a crawler that is robust, polite, and engineered well enough to be extended for indexing in HW2. Our primary challenge is to maximize domain breadth without violating etiquette or over‑engineering beyond a single machine.
2. Goals, Non‑Goals
2.1 Goals
Breadth‑First Coverage: Prefer unseen/less‑seen domains; reach 10k unique domains in pass‑1.
Politeness & Compliance: Strict robots.txt enforcement, crawl‑delay, and per‑host concurrency ≤ 1.
Robustness: Handle DNS failures, timeouts, redirects, non‑HTML types, traps; clean shutdown.
Observability: Structured logs, counters, and scripts to compute SLIs; reproducible outputs.
Modularity & Testability: Components are small, injectable, and unit‑testable.
2.2 Non‑Goals
Browser/JS execution, distributed cluster execution, sophisticated ML de‑dup/extraction.
3. Requirements
3.1 Functional
Accept seed domains/URLs via CLI.
Fetch HTML only; ignore PDFs but extract and enqueue http(s) links contained within (best‑effort regex; optional pdfminer path).
Extract links from HTML, normalize, and enqueue up to max_depth.
Enforce robots (allow/deny) and crawl‑delay; per‑host concurrency ≤ 1.
Apply exclusion rules (regex includes/excludes) and page cooling (TTL before re‑enqueue of same URL).
Persist HTML to disk; write JSONL telemetry per event.
3.2 Non‑Functional
Perf (localhost SLO): ≥ 50 pages/sec for ≥5 min; error rate ≤1%.
Coverage SLO: ≥ 10,000 unique registrable domains in first‑pass domain crawl.
Guardrails: 100% robots compliance; error rate ≤5% on public web; bounded memory/FDs.
Ethics: No stress tests on public sites; perf runs only on localhost.

4. Success Metrics (SLIs/SLOs) & Guardrails
Metric
SLI
SLO / Target
Notes
Throughput (pps, localhost)
pages / second
≥ 50 pps
Synthetic local site; politeness disabled
Unique domain coverage
count of registrable domains fetched
≥ 10,000 (first pass)
eTLD+1 definition
Robots compliance
% requests allowed by robots
100%
Never fetch if disallowed
Error rate
(#errors)/(#fetches)
≤1% (local), ≤5% (web)
Timeouts, 4xx/5xx, DNS
HTML share
% saved responses that are HTML
≥95%
Non‑HTML filtered

Guardrails: per‑host concurrency ≤1; respect crawl‑delay; bounded memory/FDs; ethical usage.
5. Architecture Overview

Key ideas:
Domain‑fair BFS frontier: min‑heap key (domain_seen_count, depth, tiebreak, url).
Registrable domain counting for coverage; hostname for robots/per‑host limits.
Robots manager holds robots cache & per‑host next‑ok timestamp.
PDF path: ignore body; harvest URLs inside PDFs and enqueue.
Filters: rule exclusions and cooldown before enqueue.

6. Components (Interfaces & Responsibilities)
6.1 Controller / CLI
Parses flags; wires components; starts N worker threads; prints heartbeats & final summary; clean shutdown.
6.2 Frontier
Structures: seen_urls:Set[str], domain_counts:Dict[host,int], heap:List[(domCnt, depth, tiebreak, url)].
Operations: push(url, depth), pop() → (url, depth), size; de‑dup; domain fairness.
First‑pass quota: while unique_reg_domains < target, only enqueue links from new registrable domains.
Cooling: gate re‑enqueue with TTL (cooldown_sec).
6.3 Robots Manager
allowed(url) → bool, delay_ms(url) → int; cache robots.txt per host; maintain next_ok_ms[host] to serialize per‑host requests and honor crawl‑delay.
6.4 Fetcher & DNS
fetch(url) → (bytes, status, content_type) with timeouts; redirects bounded; DNS cache (host→IP).
Early Content‑Type filter; cap bytes (max_bytes).
6.5 Parsers
HTML: extract <a href>; resolve relative; strip fragments; accept http/https.
PDF: regex search for https?://… in byte stream; optional pdfminer implementation behind a flag.
6.6 Filters (Role/Rule Exclusion)
Compiled regex include (wins) and exclude lists; applied before enqueue.
6.7 Storage & Telemetry
HTML path: data/{host}/{sha1(url)}.html.
JSONL events with fields {ts, event, url, host, depth, status, bytes, content_type, thread, t_ms_from_start, reason?}.
Heartbeat every 50 pages with counters.

7. Data Model
Registrable domain (eTLD+1): computed via PSL (e.g., tldextract): news.bbc.co.uk → bbc.co.uk.
Events: fetch_ok, error, robots_disallow, excluded_by_rule, cooldown_skip, pdf_links_extracted, heartbeat.

8. Algorithms & Policies
8.1 Scheduling (Domain‑Fair BFS)
Key = (domain_seen_count, depth, tiebreak). This produces breadth across hosts, then shallow depth. Tiebreak is a monotonic counter for deterministic order.
8.2 Robots & Politeness
On pop, check allowed(url). If disallowed, log and skip.
Before HTTP, wait until now ≥ next_ok_ms[host]; set next_ok_ms = now + delay_ms(url).
8.3 PDF Handling
If Content‑Type is PDF or URL ends with .pdf, do not persist the bytes. Extract URLs via regex over the byte stream; normalize and enqueue if allowed.
8.4 Exclusion Rules & Cooling
Skip URLs matching exclude unless they match include.
Maintain last_fetched_at[url]; skip enqueue until TTL passes.
8.5 10k Domain First‑Pass
CLI: --domain-seeds-csv, --target-unique-domains=10000.
Seed one URL per domain (try https→http fallback). During pass‑1, only enqueue links that would add newregistrable domains. After target is reached, switch to normal policy.

9. Public Interfaces (CLI)
Flag
Type
Default
Description
--seeds
list[str]
required
Seed URLs
--domain-seeds-csv
str


CSV of domains to bootstrap breadth
--target-unique-domains
int
10000
Stop after this many registrable domains
--max-pages
int
10000
Hard page budget
--max-depth
int
2
BFS depth limit
--workers
int
8
Thread count
--politeness-ms
int
1000
Per‑host base delay (web)
--timeout
int
10
HTTP timeout seconds
--max-bytes
int
2_000_000
Max bytes per response
--user-agent
str
CS6913Crawler/1.0
Identifier + contact
--parse-pdf-links
bool
true
Enable PDF link harvesting
--exclude-pattern
repeat
[]
Regex to exclude
--include-pattern
repeat
[]
Regex to include (wins)
--cooldown-sec
int
0
TTL before re‑enqueue of same URL


10. Edge Cases & Failure Modes
Robots unreachable → permissive but still rate‑limit per host.
Redirect chains → cap hops; de‑dup on final URL.
Session/calendar explosions → mitigate via depth caps, excludes, per‑site caps.
Non‑HTML types → skip save; PDF path extracts links.
Malformed HTML/URLs → robust normalization; drop on failure.
IDNs & multi‑level TLDs → PSL resolves registrable domain.

11. Test Strategy
11.1 Unit Tests
URL normalization; registrable domain calc; frontier ordering; robots decisions; cooldown; exclusion rules; PDF link regex; DNS cache.
11.2 Integration Tests
Local 1k–20k page site; verify breadth (unique domains with synthetic hostnames), depth behavior, robots allow/deny, cooldown.
11.3 Performance (Benchmark)
Local synthetic site; --workers 32–128, --politeness-ms 0; compute pps from logs; meet ≥50 pps.
11.4 Determinism & CI
Deterministic ordering via monotonic tiebreaker; fixtures checked into repo; tests run w/o network by mocking fetch().

12. Security, Privacy, & Ethics
Robots compliance mandatory; per‑host politeness enforced.
PII/Restricted Areas: default excludes for /login, /admin, /cart; no credentials/cookies by default; mask sensitive query params in logs if configured.
Ethical crawling: never stress public sites; performance tests only on localhost.
13. Observability, Debugging & Alerting
Structured JSONL logs with event taxonomy; verbose on -vv.
Heartbeats every 50 pages: fetched, enqueued, errors, unique_domains, frontier_size.
Post‑run scripts: pps, error distribution, top error hosts, coverage chart.
Assertions/Alerts (console): high error rate, large frontier starvation, FD near limit.

14. Rollout & Ops (Runbook)
Generate local synthetic site (20k pages) and start python -m http.server 8000.
Run crawler with --seeds http://localhost:8000/index.html --workers 64 --politeness-ms 0 --max-pages 15000.
Compute PPS via analysis script; verify ≥50 pps and ≤1% errors.
For web runs: --politeness-ms 1000, --workers 8–16, add --exclude-pattern guards; cap pages; capture logs.

15. Capacity & Performance Notes
Threads scale for I/O‑bound workload; if parser CPU dominates, consider lighter HTML parsing for perf runs.
Disk I/O: buffered writes; SSD recommended. Increase ulimit -n to ≥4096.
Queue contention: if observed, consider per‑domain queues + global round‑robin (future).

16. Risks & Mitigations
Lock contention → optimize critical sections; batch enqueues.
Robot traps → depth caps, excludes, per‑site caps.
Over‑fetching PDFs → early Content‑Type filter; cap read bytes.
Ethical concerns → strict policies; localhost for perf.
17. Alternatives Considered
Async (asyncio) vs threads: Chose threads for simplicity; async a future option.
Per‑domain queues vs single heap: Single heap is simpler; queues improve fairness under extreme scale (future).
Full PDF parsing vs regex: Regex gives 80/20 value with no heavy deps; pdfminer optional.
Focused crawler (ACHE‑style) vs breadth: Breadth matches HW1; focused is future extension.
18. Open Questions
Should we persist frontier/robots cache across runs to resume mid‑crawl?
Do we enforce a global site cap (e.g., ≤N pages per domain) for public runs?
19. Milestones
M0 Skeleton & CLI
M1 MVP HTML crawl
M2 Robots + Politeness
M3 Exclusions + Cooling + PDF links
M4 Perf bench (≥50 pps)
M5 Tests + Report
20. References
Shkapenyuk, V., & Suel, T. Design and Implementation of a High‑Performance Distributed Web Crawler(Polytechnic/NYU).
ACHE – ViDA‑NYU focused crawler (classifier‑guided link prioritization; sitemap re‑crawl; monitoring/UI).
CS 6613 Lecture slides (Indexing, I/O‑efficient sorting, robots/politeness).
Manning, Raghavan, Schütze — Introduction to Information Retrieval.

