# MVP Fusion - Cursor Plan PRD

## Executive Summary

Goal: Evolve MVP-Fusion to a robust, two-core, dual-role CPU worker architecture with bounded queues and deterministic drain/shutdown. Preserve existing logging style while extending it to queue-aware, worker-agnostic tags. Maintain current APIs and outputs, avoid architectural rewrite, and keep performance at high throughput with minimal blocking.

Key ideas:
- Two CPU processes act as dual-role workers (Convert and Compute) fed by bounded queues.
- Explicit backpressure using blocking put/get and deterministic sentinel drain.
- Small-first scheduling for conversion to avoid head-of-line blocking by large PDFs.
- Writer is single-threaded for atomic, idempotent output.
- Logging remains Fusion-style; add queue metrics and universal worker tag.

## Objectives and Non-Objectives

- Objectives:
  - Increase robustness under bursty inputs and occasional large documents.
  - Eliminate dropped tasks and premature shutdown races.
  - Keep cores busy: if resources exist, do work.
  - Maintain current CLI, pipeline stages, and output formats.
  - Preserve current logging aesthetic while adding queue-level visibility.
- Non-Objectives:
  - No full rewrite to fully-async pipeline.
  - No mandatory persistent message broker.
  - No change in knowledge JSON schema or markdown YAML ordering.

## Proposed Architecture

### Topology
- I/O Thread: discovery (files/URLs), metadata (page estimates), task creation.
- CPU Workers (2 processes): dual-role loop prefers convert tasks, else compute tasks.
- Writer Thread: drains write queue; atomic writes and renames.

### Queues (bounded)
- convert_q (mp.Queue): size 8; payload: {path, est_pages, mime, dedupe_id}.
- compute_q (mp.Queue): size 64; payload: {path or temp handle, metadata}.
- write_q (queue.Queue): size 128; payload: {doc handle, yaml, semantic_json}.

### Worker Loop (per CPU process)
1) Try convert_q (non-blocking check); if empty → block on compute_q.get().
2) Convert task: PDF→Markdown (+ base YAML); push minimal handle to compute_q.
3) Compute task: classify→normalize→extract (≈10ms); push to write_q.
4) Shutdown: sentinel per queue; workers exit when both queues drained.

### Flow
- Intake: files → PDFs to convert_q; non-PDFs → compute_q. URLs: limited concurrency download → same routing.
- Conversion: CPU-bound; small-first scheduling by est_pages; pass handles, not blobs.
- Compute: fast CPU; preload engines in process initializer to avoid per-task overhead.
- Write: single-threaded, idempotent tmp→rename, dedupe by key.

### Backpressure & Drain
- Blocking put/get with bounded capacities (no timeouts).
- task_done()/join() on queues before emitting sentinels.
- Shutdown order: stop intake → join convert_q → send convert sentinels → join compute_q → send compute sentinels → join write_q.

## Logging Strategy (Compatibility + Enhancements)

### Keep
- FusionLogLevel levels and visual style.
- LoggerAdapter API: stage(), conversion(), queue(), classification(), normalization(), enrichment(), semantics(), writer(), success().

### Enhance
- Universal worker tag: replace thread-derived tag with stable role tag: I/O, CPU-1, CPU-2, WRITER.
- Queue metrics: queue(level, message, queue_size, queue_max), plus periodic heartbeat lines:
  - produced/convert_pending/compute_pending/written/errors.
- PhaseManager integration: set phase around queue transitions; include pages processed and MB/sec estimates.

### Sample Logs
- [STAGING-IO] Queued task fileA.pdf (queue: 3/8, ram: 42%, cpu: 61%)
- [CONVERSION-CPU-1] Converted fileA.pdf in 12.3ms (pages: 7)
- [CLASSIFICATION-CPU-2] Entities: person:5, org:3 (10.1ms)
- [WRITER-WRITER] Wrote fileA.md, fileA.json
- [PERF-MAIN] convert_q: 2/8, compute_q: 11/64, inflight: 13, written: 1200, errors: 0

## Compatibility and Breakage Review

- CLI: No flags removed; add optional pipeline.queue_* settings.
- FusionPipeline API: unchanged; ServiceProcessor gains dual-queue orchestration.
- SharedMemoryPipeline: unaffected; can adopt same logging style later.
- Logging: existing calls continue working; new worker tag logic applies universally.
- Output: filenames and schemas unchanged; writer path remains idempotent.

Risks:
- Deadlocks if sentinels misordered: mitigated by explicit join-before-sentinel and per-queue sentinels.
- Starvation if convert preference too strong: mitigate with time-slice or fair policy if convert_q stays non-empty.
- IPC overhead: pass handles/paths (not blobs); preload models in process initializer.

## Performance Considerations

- Two cores fully utilized by dual-role workers; conversion prioritized to avoid starving downstream.
- Small-first conversion reduces head-of-line blocking from large PDFs.
- Blocking queues stabilize throughput under burst; no dropped tasks.
- Expected latencies: conversion ≈ <10ms/page; compute ≈ ~10ms/doc; write ≈ O(filesize).

## Configuration

pipeline:
  queue_size_convert: 8
  queue_size_compute: 64
  queue_size_write: 128
  small_first_pages_threshold: 20
  url_max_concurrency_total: 8
  url_max_concurrency_per_domain: 2
  drop_on_full: false
  queue_put_timeout_seconds: 0
  executor_mode: process  # process|thread (thread for environments without fork)

## Rollout Plan

1) Phase 0: Fixes (already proposed)
   - Define max_workers in URL path; safe temp cleanup; fix logging level typo; backpressure flags.
2) Phase 1: Enable blocking backpressure in current ServiceProcessor (threads)
   - Replace queue timeouts; implement join/sentinels drain; add heartbeat counters.
3) Phase 2: Promote CPU workers to processes (initializer loads AC, normalizer, semantic extractor)
   - Split convert_q and compute_q; dual-role loop; pass handles; keep writer thread.
4) Phase 3: Optional small-first scheduling and per-domain URL limiter.
5) Phase 4: Observability
   - Add /metrics or periodic JSON log frames for queue sizes, throughput, error rates.

## Testing Strategy

- Unit: queue drain order, sentinel handling, small-first ordering, dedupe idempotency.
- Integration: mixed PDFs/MDs; stresses with one 200-page PDF + many small docs; verify no stalls, no drops, correct outputs.
- Performance: measure docs/sec, pages/sec, CPU utilization; verify compute remains saturated and writer keeps up.
- Fault injection: converter error, network timeout, writer fs error; ensure task error records are written and pipeline proceeds.

## Migration Guidance

- Config: add new pipeline queue sizes and executor_mode; defaults keep previous behavior (threads, drop_on_full=false, blocking put/get).
- Logging: adopt universal worker tag resolver; no change to logger call sites required.
- Code changes focus: ServiceProcessor; Writer; minimal edits in CLI for backpressure flags.

## Implementation Notes

- Dual-role worker pseudocode

```python
while True:
    try:
        task = try_get(convert_q, timeout=0.0)
        if task is None:
            task = compute_q.get()  # block until compute available or sentinel
        if task is SENTINEL:
            mark_done(task.q)
            break
        if task.kind == 'convert':
            handle = convert_pdf(task)
            compute_q.put(handle)
            mark_done(convert_q)
        else:
            result = compute(handle)
            write_q.put(result)
            mark_done(compute_q)
    except Exception as e:
        log_error(e)
```

- Writer: always tmp → atomic rename; dedupe id = hash(url|path|normalized).
- Memory guard: semaphore around “active docs MB”; estimate from file size/pages.

## Open Questions

- Do we prefer strict small-first or hybrid fairness (N small, then 1 large)?
- Should SharedMemoryPipeline adopt the same queue/log style for consistency?
- Add persistent queue adapter (Redis/Rabbit) behind an interface for retries later?

## Acceptance Criteria

- Under mixed loads, no dropped tasks; graceful shutdown; logs show queue sizes and worker roles.
- Two CPU processes stay ≥80% utilized; compute throughput unchanged or better.
- Outputs identical in schema and naming; no logging regressions.
- Configuration defaults preserve current behavior with improved stability.

## Advanced Enhancements (Optional, High-Performance Track)

### Micro-batching for compute
- Batch size 4–16 per process to amortize IPC and Python overhead.
- Preserve streaming: flush partial batches on idle or timeout (e.g., 10–20ms).

### CPU process tuning
- Process initializer loads Aho-Corasick, normalizer, semantic extractor once.
- Pin CPU workers to cores (taskset or psutil affinity) to reduce cache thrash.
- Use uvloop (if async added) for lower event-loop overhead.

### IPC and memory
- Pass only handles/paths in queues; avoid large payloads.
- Optionally use shared memory (multiprocessing.shared_memory) for hot markdown text between convert→compute.
- Compress large markdown (>1MB) using zlib before IPC if needed.

### GC and Python runtime
- Disable cyclic GC in CPU workers during tight loops; re-enable periodically or on idle.
- Pre-allocate common objects/regex/patterns.
- Consider PyPy for compute stage if regex-heavy and compatible; benchmark first.

### Persistent queue (scale-out, retries)
- Adapter interface for Redis Streams/RabbitMQ/SQS; feature-flag controlled.
- At-least-once with idempotent writer keyed by dedupe id.
- Visibility timeout and retry with exponential backoff.

### Domain-governed URL throttling
- Token-bucket per domain with Open PageRank weight (major sites higher rates).
- Global cap + per-domain cap to prevent edge blocking.
- Backoff on 429/5xx with jitter.

### Observability
- Heartbeat: every 2–5s emit JSON line with queue sizes, inflight, written, errors, docs/sec, pages/sec.
- Tracing: span IDs across convert→compute→write; include file/url id.
- Health endpoints (CLI flag): /healthz (OK), /metrics (Prometheus pull text or JSON dump to log).

### OS / FS tuning
- Increase file descriptor limits (nofile) for heavy URL intake.
- Use tmpfs for temp files if memory allows; ensure cleanup.
- Use O_DIRECT-equivalent only if tested; default buffered writes suffice.

### Scheduling policies
- Hybrid small-first: process 8 small then 1 large to avoid starving big documents.
- Aging: increase priority of long-waiting convert tasks.

### Failure isolation
- Per-task timeout in compute; on timeout, fail the single task and continue.
- Circuit-breaker on repeated converter errors for a file type or domain.

### Security & correctness
- Content-type allowlist; size caps pre-download; hash input to dedupe and detect repeats.
- Atomic writes with fsync on metadata when integrity is critical.

### Rollback and feature flags
- Feature flags for: dual-queue mode, process executor, small-first, domain throttling, micro-batching.
- Canary by directory/domain; fall back to current threaded mode on flag flip.

## Extreme URL Tuning

### Current state (URL pipeline)
- Input: `--url` and `--url-file` handled in `fusion_cli.py`.
- Fetching: synchronous `requests` with `HTTPAdapter(pool_connections, pool_maxsize, max_retries=1)` in a shared `Session`; `ThreadPoolExecutor` drives concurrency for url-file.
- Size/type safety: content-length precheck; stream with chunk limit; max content size enforced; basic MIME allowlist.
- Conversion path: bytes → temp file (safe filename) → pipeline (convert/classify/enrich/extract) → rename outputs to URL-based safe filename.
- Logging: good stage logs; limited per-domain visibility; no holistic progress heartbeat.

### Identified gaps
- No per-domain throttling/rate limits; global thread pool can overload small sites.
- Limited retry/backoff (max_retries=1); no 429-aware exponential backoff/jitter; no circuit breaker by domain.
- No URL normalization/dedupe across runs; risk of duplicate work.
- HEAD preflight not used (opportunistic size/type check without downloading body when servers support it).
- Synchronous requests scale modestly; no HTTP/2 multiplexing; limited connection reuse across domains.
- Temp-files always used for URL; no pure in-memory fast-path when pipeline supports it.
- No persistent cache (ETag/Last-Modified); no content hash de-dup.
- Observability: lacks per-domain success rates, status histograms, bytes/sec, in-progress counts.

### High-performance plan

#### Fetch tier (Async, domain-governed)
- Async client: adopt `httpx` (HTTP/2, connection pooling, TLS reuse) with `asyncio` and `uvloop` (optional) for URL intake.
- Domain Governor: per-domain token bucket limiting and backoff to avoid bans; weight tokens by domain popularity/open-rank (Domain Governor pattern) [[memory:2838]].
- Concurrency:
  - Global concurrency cap (e.g., 64) and per-domain cap (e.g., 2 for small, 8 for large sites).
  - Queue: `url_q` (asyncio.Queue, size 1024) with blocking backpressure.
- Preflight:
  - Attempt HEAD: decide early on `content-length`, `content-type`, `Last-Modified`, `ETag`.
  - Respect robots.txt (configurable); skip blocked paths.
- Retries:
  - Exponential backoff with jitter; 429/503/5xx aware; cap attempts by domain; circuit breaker after N failures within T.
- Normalization/dedupe:
  - Normalize URLs (strip fragments, sort query, lowercase host, remove tracking params) and build a dedupe key.
  - Cache seen keys (in-memory LRU + optional disk-backed bloom filter/sqlite) to avoid repeats across runs.

#### Conversion tier (HTML → Markdown)
- Fast-path: prefer direct in-memory conversion when possible (no temp files) and adapt pipeline path for URL-origin `InMemoryDocument`.
- Fallback: if pipeline requires files, keep temp file path; ensure tmpfs usage when available.
- Boilerplate removal (optional): apply readability/boilerplate extraction (e.g., `readability-lxml`, `trafilatura`, `selectolax`) before Markdown to reduce noise and output size.
- Small-first ordering: prioritize small HTML (by `content-length`) to avoid head-of-line blocking.

#### Compute tier (existing)
- Reuse dual-role CPU workers; convert/enqueue compute payloads; keep 10ms per stage budget.
- Batch small docs (4–16) optionally to amortize overhead while maintaining streaming.

#### Write tier (existing)
- Idempotent writer keyed by dedupe id (normalized URL); tmp → atomic rename; write JSON only when semantic data exists.

#### Observability & health
- Per-domain metrics: success rate, status code distribution, average latency, bytes/sec, active connections.
- Global metrics: urls discovered/queued/fetched/converted/computed/written; drop/skip counts; errors by class.
- Heartbeat every 2–5s: JSON line with queue depths, inflight counts, rate, domain top-K by backlog.

### Detailed design
- Components:
  - URL Producer: reads url-file(s), normalizes, filters duplicates, pushes to `url_q`.
  - Domain Governor: async controller maintaining per-domain semaphores and token buckets; integrates failure/backoff.
  - Async Fetchers: N tasks consume `url_q`, acquire domain token, preflight HEAD, then GET with stream limits; on success, handoff to Conversion.
  - Conversion Bridge: create `InMemoryDocument` (URL metadata), run HTML→Markdown; enqueue to compute queue.
- Backpressure:
  - `url_q` bounded; conversion and compute queues bounded; all put/get blocking; deterministic drain with sentinels.
- Caching:
  - Optional HTTP cache (ETag/If-None-Match, If-Modified-Since) via `httpx.CacheControl`-like middleware or manual headers.
  - Content fingerprint (SHA-1 of canonicalized body) to avoid duplicate compute on identical pages (configurable).

### Configuration additions

pipeline:
  url_ingest:
    global_concurrency: 64
    per_domain_concurrency_default: 2
    per_domain_overrides:
      "wikipedia.org": 8
      "github.com": 8
    backoff_base_ms: 200
    backoff_max_ms: 10000
    retries: 4
    head_preflight: true
    obey_robots: false
    normalize_params_remove:
      - utm_source
      - utm_medium
      - utm_campaign
    cache:
      enabled: true
      etag: true
      last_modified: true
      persistent_seen_db: "/var/tmp/url_seen.sqlite"
    size_limits:
      max_bytes: 10485760  # 10MB
      soft_prioritize_under_bytes: 524288  # 512KB small-first
    html_processing:
      boilerplate_reduction: true
      readability_min_text_chars: 500

### Optional Python techniques/tools
- `httpx` (async, HTTP/2, connection pooling), `uvloop` for lower latency event loop.
- `aiodns` for async DNS; `brotli` for faster compressed transfers; enable `httpx`/`h2`.
- Readability/boilerplate: `readability-lxml`, `trafilatura`, `selectolax` (fast CSS-like parser), `lxml` for robust HTML.
- Robots/URL utilities: `reppy` or `robotexclusionrulesparser`, `tldextract`, `yarl`.
- Dedupe: `pybloomfiltermmap3` or `diskcache`, SQLite for persistency.
- Telemetry: `prometheus-client` (pull) or structured JSON logs; `rich`/`textual` for local progress (optional).

### Rollout steps
1) Phase A: Replace thread pool in `process_url_file` with async fetcher wrapper (keep CLI the same); use httpx with limited global concurrency; maintain shared session-like pool.
2) Phase B: Add Domain Governor with token buckets and per-domain caps; implement 429/5xx backoff + jitter; circuit breaker.
3) Phase C: Add URL normalization/dedupe and persistent seen-db; add HEAD preflight and ETag/Last-Modified cache.
4) Phase D: Enable boilerplate reduction path behind flag; small-first prioritization by size.
5) Phase E: Hook into existing compute/write queues; add per-domain and global heartbeat metrics to logs.

### Expected outcomes
- Stable high-throughput ingestion of very large URL lists with minimal bans/blocks.
- Reduced compute waste via dedupe and boilerplate reduction.
- Better latency distribution (small-first) and resilient behavior under rate limiting.
- Clear visibility per-domain to quickly tune overrides and resolve bottlenecks.

## Extreme JavaScript Extraction

### Problem
Modern sites often ship minimal HTML and hydrate via JavaScript (React/Vue/Next/Nuxt, SPA). Pure HTML fetching misses critical content. We need a high-performance approach that avoids full browser engines when possible, but remains capable of rendering when required.

### Strategy: Tiered, render-as-needed
Prioritize cheaper, deterministic techniques first; escalate to rendering only when necessary.

- Tier 0: Static HTML path (existing)
  - If content density and semantic markers indicate server-rendered HTML, keep current conversion path.

- Tier 1: Initial state extraction (no JS execution)
  - Detect common app frameworks and embedded bootstraps:
    - Next.js: `__NEXT_DATA__`, `id="__NEXT_DATA__"` JSON
    - Remix/React: window.__INITIAL_STATE__, window.__APOLLO_STATE__
    - Redux stores, `data-state`, `data-hydration-state` attributes
    - JSON-LD (`application/ld+json`) and microdata
  - Parse these blocks (no DOM execution) and convert to structured markdown sections + YAML.

- Tier 2: API/backing-data discovery (no JS execution)
  - Discover and query REST/GraphQL endpoints referenced by scripts or link tags:
    - Look for `fetch(`/api`, `/graphql`, signed URLs, paginated endpoints)
    - Attempt GraphQL introspection (if enabled) and perform lightweight queries identical to the page’s.
  - Respect robots and rate limits (via Domain Governor) and cache responses.

- Tier 3: Lightweight prerender (minimal execution)
  - Use a small, shared renderer only for pages that fail Tiers 1–2 (strict budget: e.g., 1–2 processes):
    - Playwright/Chromium with resource blocking (images, fonts, media, ads, trackers, analytics).
    - 2–5s timeout, network-idle or specific DOM selector to mark readiness.
    - Intercept network to record XHR/GraphQL calls and persist for reuse.
  - Output: DOM innerText + relevant HTML → markdown, plus captured API payloads → YAML/JSON sections.

- Tier 4: Remote prerender (optional)
  - For heavy/hostile sites, offload to a stateless prerender service (Dockerized) behind a queue with strict quotas.

### Detection and routing
- JS-heavy heuristics (no execution):
  - HTML size < 30KB, presence of large `*.chunk.js`, root div like `id="__next"`, `id="app"`, few text nodes
  - Multiple `<script type="module">` with large sources
- Decision tree:
  1) Static indicators → Tier 0
  2) Bootstraps present → Tier 1
  3) API endpoints discoverable → Tier 2
  4) Otherwise → Tier 3 (renderer) with strict budgets

### Renderer performance rules (when used)
- Block resources: images, video, fonts, css (unless needed), third-party trackers
- Set `userAgent`, accept-encoding (gzip, br), language, viewport small
- `wait_until`: network idle with max cap (e.g., 2s idle or 5s total)
- Request interception: allow document, xhr/fetch; abort others
- Reuse browser processes and contexts; maintain a small pool (size = 1–2)
- Per-domain concurrency = 1 by default to reduce ban risk; governed by Domain Governor

### Integration with pipeline
- URL intake: add `content_mode` decision to URL metadata (static, initial_state, api, rendered)
- Conversion phase:
  - Tier 1–2: Create `InMemoryDocument` directly with markdown sections derived from JSON; annotate YAML with `content_mode`
  - Tier 3: Feed prerendered HTML into existing HTML→Markdown converter and continue normally
- Compute and write stages: unchanged; additional YAML sections provide richer context

### Observability
- Per-mode counters: static/initial_state/api/rendered
- Per-domain renderer usage rate and average render time; XHR count, bytes fetched
- Failure classes: blocked by robots, 403, 429, script crash, timeout

### Configuration additions

pipeline:
  js_extraction:
    enabled: true
    max_renderer_processes: 2
    max_render_time_ms: 5000
    network_idle_ms: 1000
    block_resource_types:
      - image
      - media
      - font
      - stylesheet
      - websocket
      - other
    allow_resource_types:
      - document
      - xhr
      - fetch
    prefer_initial_state: true
    prefer_api_discovery: true
    enable_graphql_introspection: false
    initial_state_keys:
      - __NEXT_DATA__
      - __APOLLO_STATE__
      - __INITIAL_STATE__
    jsonld_extract: true
    api_capture: true
    per_domain_render_concurrency_default: 1

### Optional Python tools/techniques
- Initial-state/metadata:
  - `extruct` for JSON-LD/microdata/RDFa
  - `selectolax` for fast HTML parsing; `lxml` where robustness needed
- API discovery:
  - `httpx` for XHR/GraphQL calls; `gql` for GraphQL queries (if enabled)
- Lightweight render (when necessary):
  - `playwright` with request interception; persistent browser, re-used contexts
  - `pyppeteer` (older), but prefer Playwright for stability
- HTML→Markdown:
  - Keep current converter; optionally add boilerplate reduction (`trafilatura`, `readability-lxml`)
- Performance:
  - Reuse connections (HTTP/2), domain-limited concurrency, token buckets
  - Cache API responses and initial-state blobs keyed by URL hash

### Rollout plan
1) Implement Tier 1 initial-state and JSON-LD extraction; annotate YAML; measure coverage.
2) Add Tier 2 API discovery for common patterns and GraphQL (opt-in introspection).
3) Introduce Tier 3 renderer pool behind feature flag; block heavy resources; 1–2 processes; strict timeouts.
4) Integrate Domain Governor limits for rendered sites; add per-mode metrics and logging.

### Expected outcomes
- Majority of JS sites handled without rendering (Tiers 1–2), preserving high throughput.
- Renderer used sparingly, under tight budgets, with minimal impact on overall performance.
- Richer structured outputs via initial-state/API capture, improving downstream extraction quality.
