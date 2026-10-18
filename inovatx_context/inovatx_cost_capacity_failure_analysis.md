# INOVATX Development Cost, Capacity, and Failure-Point Assessment

**Prepared:** 2026-10-16  
**Purpose:** Pre-approval planning estimate for the first-client EdTech MVP  
**Currency:** USD  
**Estimate class:** Indicative, pre-build; replace with vendor quotes and load-test results before budget approval

## Executive summary

- The source documents describe a greenfield first-client MVP: Django Core, Moodle, PostgreSQL/RLS, Redis/Celery, FastAPI AI coaching, payment/license activation, and operational readiness. No application source code or measured workload is present in the supplied workspace.
- Development is assumed to be performed by the founder: paid AI is reserved for logical/critical architecture analysis and assessment; coding and debugging use free tools/options. For the remaining pre-deadline work window, budget **about $30-$700 in incremental development cash costs**, primarily for a paid analysis assistant and optional staging/API tests. This excludes the founder's time and ongoing production hosting/AI usage.
- For a pilot, reserve **$100-$300/month** for a single 8-vCPU/16-GB application VPS plus off-host backups and basic operational services. This is not an HA production design and does not prove the PRD's 500-concurrent-user target.
- At **100 active users**, modeling one AI interaction per learner every 10 minutes gives an average **0.167 AI evaluations/s** during use, approximately **30.8 modeled database transaction units/s** alongside 10 app requests/s, and about **833 provider tokens/s** (667 input + 167 output). Burst-test at twice this rate; separately test up to 100 simultaneous SSE streams.
- At the selected 4,000-input/1,000-output token profile, model API spend is approximately **$0.00028 per Llama 3.1 8B interaction** or **$0.00098 per Qwen3 30B A3B interaction** before the API router fee. A 1,000-interaction monthly allowance for 100 seats (100,000 interactions) would cost about **$30 or $103/month**, respectively, including the cited 5.5% standard-plan fee. Provider limits, model quality, privacy terms, and regional availability need validation.
- A single VPS is a material outage and data-loss risk. The design also has unverified performance, a potentially contradictory provisioning SLO/retry policy, provider rate-limit risk, and an unresolved browser-to-private-AI streaming path.

## 1. Source scope and assumptions

Source documents reviewed: the PRD, UML/model views, Phase 0 decision log, project roadmap, completion checklist, executive sign-off gate, and supplied Word/PowerPoint documents in `docx/`.

Important source constraints carried into this estimate:

- The completion/sign-off documents authorize **Phase 0 only** until the relevant decisions and gates are approved. This assessment is a budget/capacity input, not implementation authorization.
- The design targets a single Docker Compose VPS, with a decision-log candidate size of 8 vCPU, 16 GB RAM, and 200 GB NVMe. The PRD separately says at least 500 concurrent quiz takers, but no benchmark evidence is supplied.
- One interaction is pre-reserved as 5,000 tokens, then reconciled. The signed-off decision log's fair-use policy defines `/socratic-eval` as critical (returns a clear limit error on exhaustion) and `/hint` ancillary endpoints as downgradable to static/lightweight responses. The allowance amount itself (interactions/month per seat) is captured in decision D17: **1,000 interactions/month for the Learner tier**, derived from the study pattern (48 interactions/day × 20 days = 960 minimum; 1,000 with 40 headroom). The 500-interaction figure in PRD §5.2 is the prior baseline; D17 supersedes it for pilot pricing and tier design.
- Mastery is sourced from the Moodle gradebook at request time. Whether this can be served from cache or must be a synchronous remote request is not specified.
- The operational targets include p95 AI first byte under 1.5 seconds, p95 payment-to-Moodle provisioning under 3 seconds, and 99.5% monthly uptime.

The workload is a model, not a forecast:

| Input | Planning assumption |
|---|---:|
| Simultaneous active users for this estimate | 100 |
| Application/Moodle dynamic actions per active user | 1 every 10 seconds |
| AI coaching interaction per active user | 1 every 10 minutes while actively using the service |
| Average AI prompt / completion for cost model | 4,000 input / 1,000 output tokens |
| Reserved allowance | 5,000 tokens/interaction, as specified in the decision log |
| Active school usage window for monthly study allowance | Up to 8 hours/day, 20 days/month = 160 hours |
| Month for continuous-rate calculations | 30 days = 2,592,000 seconds |
| Database transaction units | 3 per ordinary application request + 5 per AI request; a modeling assumption, not a schema benchmark |
| Currency | USD; vendor taxes, FX conversion, payment fees, and network egress are excluded unless explicitly shown |

The 4k/1k token profile is a pricing example, not a claim that each prompt will fit. Rubrics, multi-turn history, and oversized student submissions can increase input usage; actual usage must be collected from provider-reported token counts.

## 2. Development cost estimate: founder + AI

This estimate assumes the founder does all implementation, product decisions, integration, testing, deployment, and operations work. Paid AI is used only for higher-value logical/critical system analysis and assessment; code generation, routine coding assistance, and debugging use free tools/options. No contractor or employee labor is budgeted. The founder's time is therefore **$0 cash outlay**, not zero effort or zero economic value.

The original roadmap has about seven weeks from October 13 to December 1. As of October 16, only **46 calendar days** remain. AI assistance does not remove the founder's responsibility for reviewing generated code, understanding security boundaries, fixing integration issues, and verifying the system. The dated plan below targets a working MVP by **November 28**, three days before the stated deadline, and assumes a very intensive solo schedule.

### Incremental development cash budget through November 28

| Cost item | Planning basis | Cash estimate |
|---|---|---:|
| Founder implementation labor | No salary/contractor cost charged | **$0** |
| Paid AI for architecture/logical review | One existing or new paid plan for about 6 weeks; budget placeholder $20-$50/month | **$30-$75** |
| AI product/model integration tests | Prefer local/free tests; allow up to 50,000 low-cost Llama/Qwen evaluation calls at rates in §4.1 | **$0-$52** |
| Coding/debugging assistants | Free options only, as specified | **$0** |
| Staging/test infrastructure | Reuse local equipment where possible; otherwise allow up to $300/month for about 6 weeks | **$0-$450** |
| Domain, storage, and incidental test services | Only if not already available | **$0-$100** |
| **Indicative incremental development cash total** | Rounded planning range; excludes production operation | **$30-$677** |

Use **$30-$700** as the expected development cash envelope if local/free staging is practical; budget **up to $700** if a separate temporary staging server is needed. If the paid AI plan is already active and would be paid regardless, its *incremental* development cost may be $0. Plan prices are placeholders, not a vendor quote: use the selected service's actual billing. Keep AI API tests behind a spend cap; use synthetic/anonymized test prompts rather than learner data.

### Economic value of founder time (optional, not cash spend)

For comparison only, track actual hours and multiply by a personal rate if an economic-cost figure is needed. This schedule reserves **about 414 focused hours** before the November 28 target. At $30/hour that is $12,420 of founder time; at $75/hour it is $31,050. Neither amount is an expected cash payment. This is a highly demanding schedule, and actual hours may be higher if unfamiliar integrations or defects arise.

The estimate excludes production hosting and runtime AI usage (covered in later sections), payment gateway fees, taxes, content authoring, legal/compliance review, and any paid human support. It also does not represent a guaranteed delivery date: the sign-off documents authorize Phase 0 only until later gates are approved.

### Solo founder weekly schedule to beat the deadline

Target: **feature-complete and launch-validated by November 28, 2026**, preserving November 29-30 as contingency before the December 1 deadline. Focused hours exclude breaks and unrelated business/personal work.

| Dates | Hours to reserve | Main deliverable / phase focus | Exit evidence |
|---|---:|---|---|
| Oct 16-18 | 24 h | Close Phase 0 decisions, freeze first-client scope, local Docker/service baseline and acceptance checklist | Approved decisions, runnable baseline, ordered critical path |
| Oct 19-25 | 65 h | Phase 1: Django foundation, schema, tenant context, PostgreSQL RLS and isolation tests | Migrations, bootable core, RLS tests pass with production-like DB role |
| Oct 26-Nov 1 | 70 h | Phase 2: RBAC, organization/user onboarding, license/payment state and activation skeleton | Tenant/role tests, onboarding tests, mock payment path |
| Nov 2-8 | 70 h | Phase 3: Moodle user/cohort provisioning, retries, SSO and end-to-end learning launch | Individual + institutional provisioning and SSO smoke tests |
| Nov 9-15 | 65 h | Finish Phase 3 edge cases; Phase 4: FastAPI, provider adapter, SSE, usage reservation/ledger | AI stream end-to-end; quota concurrency and provider-failure tests |
| Nov 16-22 | 65 h | Finish Phase 4; Phase 5: payment/webhook idempotency, reconciliation, observability, restore/rollback checks | Full payment-to-learning-to-AI path; critical alerts and restore evidence |
| Nov 23-28 | 55 h | Phase 5/6: fix blockers, performance/security regression, pilot data, launch checklist and go/no-go | 100-user staged load test, recovery/failure tests, signed readiness decision |
| **Total** | **414 h** | **About 66 focused hours/week averaged across the remaining 44 days** | **Target complete Nov 28; Dec 1 remains the formal deadline** |

This requires roughly **9-12 focused hours per working day on six days each week**, depending on the week. It leaves little slack and assumes no major scope changes, procurement delays, external Moodle/payment-provider blockers, or foundational redesign. If that pace is not sustainable, reduce scope to the smallest client-critical path and negotiate a later launch; do not omit tenant-isolation, payment correctness, backup/restore, or end-to-end verification just to preserve the date.

## 3. Capacity estimate in QPS/TPS terms

### 3.1 Modeled peak for 100 concurrent users

| Workload | Derivation | Modeled rate |
|---|---|---:|
| Application/Moodle dynamic HTTP requests | 100 users / 10 s | 10 requests/s |
| AI evaluations | 100 users / 600 s | 0.167 evaluations/s |
| Modeled DB transaction units | (10 x 3) + (0.167 x 5) | 30.8 transactions/s |
| Provider input token throughput | 0.167 x 4,000 | 667 input tokens/s |
| Provider output token throughput | 0.167 x 1,000 | 167 output tokens/s |
| Provider total token throughput | 0.167 x 5,000 | 833 tokens/s |
| SSE connections | Up to every active learner streaming together | Up to 100 open streams |

Use **20 application requests/s, 0.333 AI requests/s, and approximately 61.7 DB transaction units/s** as an initial 2x average-rate burst test. Also test 100 AI streams opening over a short burst, not just a smooth average. Provisioning, bulk enrollment, and grade/webhook traffic are bursty and are not included in the steady quiz workload.

The “DB transaction unit” is deliberately not called a query: a database transaction may contain several SQL queries, and a SQL query may not equal one transaction. Instrument actual SQL statements, transaction duration, lock waits, connection-pool occupancy, and rows read/written. Report both queries/s and committed transactions/s from the load test.

### 3.2 Allowance for the intended study pattern

At one AI interaction every 10 minutes, a learner using AI throughout an **8-hour day** makes **48 interactions/day**. Across **20 study days**, that is **960 interactions/month**. Thus the previous 500-interaction allowance covers only about 10.4 full study days at this cadence. A sensible entry allowance should therefore be at least 1,000 interactions/month, with a daily cap and static hints after quota exhaustion.

For 100 concurrent active learners at this cadence:

- Average AI request rate while they are using the service: **100 / 600 = 0.167 AI requests/s**.
- Usage at 8 hours/day for 20 days: **96,000 AI interactions/month**.
- A 1,000-interaction tier for each of 100 learners allows up to **100,000 interactions/month**.
- At twice the average request rate, test at least **0.333 AI requests/s** and **1,667 provider tokens/s**, while separately testing short bursts of up to 100 simultaneous SSE connections.

The QPS estimate is an average; classroom exercises can synchronize learners and create a much sharper burst. Enforce per-user daily caps, an organization-wide concurrency/rate limit, and fair queueing so an institutional cohort cannot exhaust provider rate limits at once.

### 3.3 Hosting cost per application request

Using a planning operating budget of **$100-$300/month** for the single-node pilot stack and assuming 10 HTTP requests/s continuously for 30 days:

- Monthly application requests: 10 x 2,592,000 = **25.92 million**.
- Infrastructure-only cost allocation: **$3.86-$11.57 per million application requests**, or **$0.0000039-$0.0000116/request**.
- At 1 HTTP request/s, the same fixed budget allocates to **$38.58-$115.74 per million requests**.

This allocation is not a marginal cloud tariff and it is not a capacity guarantee. It distributes fixed hosting spend over assumed requests. AI model charges are separate; so are support labor, payment fees, and potential bandwidth/storage overages.

## 4. AI provider cost and limits

### 4.1 Token-price model

Rates below were read from the OpenRouter public model catalog on 2026-10-16. They are provider/model-specific catalog rates and can change; the public pricing page states a **5.5% fee on standard pay-as-you-go credit purchases**. Model availability and the rate of the provider selected by routing must be rechecked before launch.

Formula for one modeled interaction:

`cost = (4,000 x input_rate_per_token) + (1,000 x output_rate_per_token)`

| Model candidate | Input / 1M tokens | Output / 1M tokens | Model cost / interaction | Cost / 1M interactions | 50k interactions, incl. 5.5% fee |
|---|---:|---:|---:|---:|---:|
| Meta Llama 3.1 8B Instruct | $0.05 | $0.08 | $0.00028 | $280 | **$14.77** |
| Qwen3 32B | $0.08 | $0.28 | $0.00060 | $600 | **$31.65** |
| Qwen3 30B A3B Instruct 2507 | $0.12 | $0.50 | $0.00098 | $980 | **$51.70** |
| Meta Llama 3.3 70B Instruct | $0.59 | $0.79 | $0.00315 | $3,150 | **$166.16** |

For context, at **250,000 interactions/month** (500 seats each consuming 500 interactions), estimated API spend including the 5.5% fee is approximately **$73.85 for Llama 3.1 8B**, **$158.25 for Qwen3 32B**, **$258.47 for Qwen3 30B A3B**, or **$830.81 for Llama 3.3 70B**. At 500 seats each using a 1,000-interaction tier allowance, the 500,000-interaction full-use cost doubles these amounts. Taxes, currency conversion, and provider-specific surcharges are excluded.

### 4.2 Cost at sustained peak

At the modeled 100-user rate of **0.167 AI requests/s**, if sustained 24/7 for 30 days this would generate about **432,000 interactions/month**. At the rates above, API costs including the 5.5% fee would be approximately:

| Model | Estimated monthly API cost at 0.167 AI requests/s, 24/7 |
|---|---:|
| Llama 3.1 8B | $128 |
| Qwen3 32B | $274 |
| Qwen3 30B A3B | $447 |
| Llama 3.3 70B | $1,435 |

This is intentionally a stress calculation: the assumed users are active around the clock, unlike an 8-hour school day, and it exceeds the 100,000-interaction cap of 100 entry-tier seats. At the 8-hour/day, 20-day pattern, estimated AI usage is **96,000 interactions/month**, costing about **$28 with Llama 3.1 8B** or **$99 with Qwen3 30B A3B**, including the 5.5% fee. Actual usage and actual billed prompt/completion tokens must be measured.

At 0.167 AI requests/s, a 5,000-token average asks the provider path to sustain roughly **833 tokens/s** on average, or about **1,667 tokens/s** at 2x burst. The provider's maximum concurrent requests, tokens/s quota, regional routing and tail latency are not guaranteed by the per-token price. Confirm these in a paid load test; a cheap model price does not imply enough throughput to meet the 1.5-second first-byte target.

### 4.3 Suggested student plans and pricing

Recommended structure: **three paid tiers plus a limited free trial**. Keep these as monthly student subscriptions initially; offer schools pooled seat plans with a minimum monthly organization fee/seat commitment as described below.

The following are **USD-equivalent pilot price hypotheses**, not market research or final local-currency prices. They assume Qwen3 30B A3B as the conservative budget model, 4,000 input + 1,000 output tokens per interaction, and the 5.5% router fee. The AI cost is the cost if a student uses the whole allowance; it excludes payment processing, taxes, customer support, and allocated hosting.

| Tier | Monthly price hypothesis | Monthly AI interactions | Daily cap | Study-time equivalence at 1 interaction/10 min | Full-use Qwen AI cost | Full-use Llama 3.1 8B cost |
|---|---:|---:|---:|---|---:|---:|
| Trial | $0 | 100 total | Up to 10/day | About 2 hours/day for up to 10 days | $0.10 | $0.03 |
| Learner | **$7.99** | **1,000** | **50/day** | Meets 8 hours/day for at least 20 days (48 needed/day) | **$1.03** | **$0.30** |
| Study | **$12.99** | **1,500** | **75/day** | About 12.5 hours/day for 20 days at the assumed cadence | **$1.55** | **$0.44** |
| Intensive | **$19.99** | **2,000** | **100/day** | About 16.7 hours/day for 20 days at the assumed cadence | **$2.07** | **$0.59** |

The 1,000-interaction Learner tier is the minimum recommendation per **D17**, for the stated goal: 8 hours × 6 interactions/hour × 20 days = **960 interactions**, with 40 interactions of headroom. A 50/day cap lets a high-engagement learner use up to 8 hours 20 minutes of AI help in a day while preventing one unusually busy day from consuming the entire monthly allowance. Daily caps are a product policy assumption per D17; validate them with pilot usage. Unused daily allowance should not accumulate above the monthly cap.

At 100 paid seats using the Learner allowance, full usage is up to **100,000 interactions/month**. Qwen AI costs about **$103/month** or Llama 3.1 8B about **$30/month**. At 500 fully used Learner seats, this scales to 500,000 interactions and about **$517/month with Qwen** or **$148/month with Llama**, before other operating costs.

### 4.4 Cost recovery and institutional pricing

Compare plans using a contribution model, not AI spend alone:

`contribution per seat = subscription revenue - AI usage - payment fees - allocated hosting/storage - support/service costs - taxes`

At 100 seats, the pilot hosting estimate of $100-$300/month allocates to **$1-$3/seat/month**; the rough resilient-hosting placeholder of $500-$1,500/month allocates to **$5-$15/seat/month**. At 500 seats, that same resilient estimate allocates to **$1-$3/seat/month**. These allocations exclude staffed on-call and can change with actual load and data needs.

Therefore, the proposed $7.99 entry price may leave approximately **$3.96-$5.96/seat** before payment fees, support, taxes, and other overhead at 100 pilot seats on the pilot host when Qwen is fully used. It can be loss-making at 100 seats on the resilient-hosting estimate's high end. At 500 seats, using the same $500-$1,500 resilient estimate and full Qwen use, the $7.99 Learner plan leaves around **$3.96-$5.96/seat** before payment fees, support and taxes.

For institutional sales, use pooled allowances with explicit per-seat caps and a minimum monthly organization/platform fee or minimum seat commitment. This ensures small schools contribute to fixed hosting and support costs rather than assuming high volume will arrive. Set the minimum from actual local payment fees, support burden, target gross margin, and currency/tax treatment; no definitive school fee can be responsibly set from the current documents alone. Review usage and unit economics after a representative pilot before locking prices.

### 4.5 Recommended low-cost rollout

1. Benchmark Llama 3.1 8B and Qwen3 30B A3B on a fixed set of representative questions, rubrics, languages, and incorrect student workings. Score Socratic behavior, factual/rubric alignment, refusal to reveal final answers, and student readability. Do not choose on price alone.
2. Start `/socratic-eval` on the least expensive candidate that passes the educational quality gate. Use static, pre-authored hints or a lightweight model for ancillary `/hint` requests.
3. Record prompt/completion tokens, model, latency to first byte, total latency, provider status, and rubric quality outcome per request. Set hard monthly and daily spend caps and alert before the cap.
4. Consider a more capable model only for rubric-defined low-confidence cases, after measuring the escalation rate. The decision log currently says critical `/socratic-eval` errors on exhaustion; do not silently downgrade this endpoint contrary to that decision.
5. Review data processing terms, retention, training use, region/data residency, and student-data minimization before sending real learner records to an external router/provider.
6. Do not self-host these models on the proposed 8-vCPU/16-GB CPU VPS. It is not an inference GPU server. Self-hosting at interactive latency and concurrency needs a separate GPU capacity test and quote; add the GPU/instance cost, redundancy, model operations, and power/egress before comparing it with metered APIs.

## 5. Hosting and running costs

### Pilot: single-node prototype

| Cost component | Monthly planning range |
|---|---:|
| 8-vCPU / 16-GB / 200-GB class VPS (candidate in decision log) | $70-$180 |
| Off-host database/WAL backups and object storage | $10-$40 |
| Domain, email/alerts, basic monitoring and operational services | $20-$80 |
| **Indicative pilot running subtotal** | **$100-$300/month** |

These are planning allowances, not a selected-provider quote. Region, traffic egress, backup retention, taxes, and support plan change the bill. Payment processing fees are usage-based and excluded. The above does not include the AI API spend in Section 4.

### Production resilience

The pilot estimate has no independent failure domain. As a rough planning placeholder, a modest resilient design with separate application capacity, managed/redundant database and cache, load balancing, off-site backups, monitoring, and support allowance could be **$500-$1,500+/month**, before AI usage and staffed on-call. Obtain region-specific quotes and define the actual availability target before adopting this range.

### Operational staffing

Infrastructure cost is not the same as operating cost. A 24/7 response commitment requires named on-call coverage, monitoring ownership, security/patch work, backup-restore drills, and incident response. Price that labor separately; it can exceed the VPS bill by an order of magnitude.

## 6. Failure points and UX/client-loss risks

| Priority | Failure point | User/client consequence | What to measure or do before launch |
|---|---|---|---|
| Critical | Single VPS hosts ingress, Moodle, Django, databases, Redis, workers, and AI orchestration | Host, disk, kernel, or maintenance incident takes down all services; no failover | Define recovery owner and RTO/RPO; store backups/WAL off-host; test restore; isolate critical data services or add a second failure domain before production commitments |
| Critical | 100/500 concurrency claims have no benchmark | CPU, RAM, PHP worker, DB connection, or disk I/O exhaustion; slow pages/timeouts | Load test representative Moodle pages/quizzes, Django APIs, AI streams, and mixed traffic at 100 users and PRD target 500; set worker/pool limits and test twice expected burst |
| Critical | AI provider queue, rate limit, regional network, or outage | Coaching stalls, 429/5xx responses, or p95 first token exceeds 1.5s | Paid provider test at required concurrent requests and token/s; explicit connect/read timeouts, bounded retries, circuit breaker, provider status alert, and safe UI state |
| Critical | Private FastAPI versus browser SSE route is unresolved | Browser cannot reach an internal Docker address; making it public without auth exposes an expensive endpoint; proxying incorrectly can stall streams | Choose the trust path explicitly: Moodle/Django backend streams or securely relays authenticated SSE. Validate Nginx buffering, idle/read timeouts, keepalives, disconnect cancellation, origin/auth, and rate limits |
| High | Moodle gradebook API called synchronously on each AI request | Extra network round trip and Moodle load on the first-token critical path; Moodle slowdown blocks tutoring | Measure gradebook p95 and failure modes. Cache per-topic mastery with explicit freshness and invalidation, or remove it from the synchronous path if approved |
| High | 5,000-token pre-reservation / post-call reconciliation and pooled allowance contention | Row-lock hotspots, unfair reservation races, stranded reservations after worker crash, or inaccurate spend | Atomic ledger tests under concurrency; unique idempotency key per interaction; reservation expiry/reaper; reconciliation and refund path; avoid a single heavily contended organization counter |
| High | Monthly allowance or daily cap does not match the promised study pattern | Learners may hit the cap before completing 20 study days and lose access to core `/socratic-eval` | Set Learner tier to at least 960/month; proposed 1,000/month and 50/day; show remaining quota, monitor exhaustion, provide static hints, and test reset timing |
| High | Provisioning p95 <3s conflicts with retries of 1s/5s/25s | One retry can exceed the 3-second p95; users wait for account/cohort access or see partial activation | Resolve which timer is contractual and what counts as failure. Separate first-attempt latency from eventual completion/recovery; define queue age, terminal state, and user-visible pending status |
| High | Moodle/PHP concurrency and DB connections compete on same host | Quiz pages become slow even when AI calls are isolated; PHP worker exhaustion creates a queue | Track Apache/PHP worker saturation, Moodle DB pool, slow queries, lock waits, cache hit ratio, host memory and swap; protect DB with connection limits |
| High | Redis/Celery is a shared queue/cache dependency | Redis memory pressure/restart can delay provisioning and webhooks; retries can create a backlog or retry storm | Queue-depth/oldest-message alerts, durable task semantics, bounded exponential backoff with jitter, idempotent handlers, dead-letter inspection, and Redis persistence/recovery test |
| High | SSE/proxy buffering, connection timeout, or client disconnect handling | Spinner or blank response despite a successful model call; leaked model work and unnecessary charges | End-to-end browser tests through the real Nginx route; disable buffering where appropriate; cancel upstream generation on disconnect; emit keepalive/status events |
| High | Payment/webhook duplicates, replay, or out-of-order delivery | Duplicate activation/provisioning, incorrect license state, or payment support burden | Signed/versioned events, timestamp and replay checks, per-endpoint idempotency, state-transition validation, daily reconciliation, DLQ alerts and manual recovery runbook |
| Medium | Tenant-context/RLS or pooled-connection leakage | Cross-tenant data exposure, or fail-closed errors that block legitimate traffic | RLS integration tests using the production DB role and pooled connections; verify `SET LOCAL` transaction boundaries; test missing context and Celery tenant context |
| Medium | Local log/backup growth and retention on 200-GB disk | Disk fills; PostgreSQL, Moodle uploads, or logs stop accepting writes | Disk/backup/WAL growth alerts, retention tests, off-host log/archive policy and capacity forecast. Audit logs must not be retained only on the failing host |
| Medium | External model privacy/residency or provider policy change | Data-handling breach or forced model/provider outage | Minimize/pseudonymize prompt fields, review provider DPA/retention/region, version model configuration, and keep a tested alternate route |

### SLO notes that need an explicit decision

- **Resolved per D18:** The provisioning decision defines a 3-second p95 timer for first-attempt completion only, measured continuously through retries (backoffs 1s/5s/25s). A separate recovery SLO tracks successful completion including retries within 30 seconds p95, with user-visible pending status during retry. First-attempt latency and recovery time are reported separately.
- **Resolved per D19:** The 1.5-second AI target is measured inside FastAPI through first SSE byte. Browser-observed first-token latency (including network + render delay) is tracked as a secondary metric to capture the full learner experience.
- 99.5% monthly uptime allows roughly **3 hours 36 minutes of downtime in a 30-day month**. A single VPS has no automatic failover and may not meet this objective through provider maintenance or host failure (see D10 for VPS sizing).

## 7. Gate recommendations before approval

1. Confirm MVP scope, role/lifecycle/payment decisions, and actual launch approval status. Current gate documents say Phase 0 only is authorized; estimates do not remove that gate.
2. Approve an initial founder-led development cash envelope of **$30-$700** through the November 28 target, then separately approve recurring hosting, runtime AI, and operational-support budgets. Track founder hours independently; do not interpret the cash estimate as the economic value of the founder's time.
3. Decide whether the first launch promises 100 concurrent users or the PRD's 500. Treat the unbenchmarked 8-vCPU/16-GB host as a candidate baseline only.
4. Run a staged load test at 100 concurrent learners: 10 app requests/s, 0.167 AI requests/s and 833 provider tokens/s modeled, a 2x average-rate burst, 100 simultaneous SSE streams, and a 60-minute soak. Capture p50/p95/p99, HTTP and SQL QPS, DB TPS/locks, pool saturation, RAM, CPU, Redis queue depth, AI rate-limit/errors, token counts, and browser-observed latency.
5. Resolve AI allowance semantics and test exhaustion/atomic reservation with concurrent requests. Set provider account spend limits and alerting before live learner traffic.
6. Test failure paths: provider timeout/429/5xx, Moodle unavailable, Redis restart, DB failover/restore, duplicate payment webhook, worker crash mid-reservation, SSE disconnect, full disk, and tenant context absent.
7. Approve an availability and recovery architecture (including off-host backups and restore exercise) before making client-facing uptime claims.

## 8. Pricing and source references

Prices are snapshots, not fixed quotes. Recheck rates, terms, supported regions, model availability, and limits before deployment.

- [OpenRouter public model catalog API](https://openrouter.ai/api/v1/models?output_modalities=all) — per-model input/output `pricing` values used above; catalog is dynamic.
- [OpenRouter pricing and fees](https://openrouter.ai/pricing) — Standard plan 5.5% credit-purchase fee; model inference billed at provider list prices.
- [Qwen3 30B A3B Instruct 2507 model/API page](https://openrouter.ai/qwen/qwen3-30b-a3b-instruct-2507/llms.txt) — model/API identity and streaming support.
- [Llama 3.1 8B Instruct model/API page](https://openrouter.ai/meta-llama/llama-3.1-8b-instruct/llms.txt) — model/API identity and streaming support.
- [Llama 3.3 70B Instruct model/API page](https://openrouter.ai/meta-llama/llama-3.3-70b-instruct/llms.txt) — higher-cost comparison model.
- [Hetzner Cloud](https://www.hetzner.com/cloud/) and [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets) — vendor calculators for region-specific infrastructure quotes. This report does not select either vendor or present a quote from them.
