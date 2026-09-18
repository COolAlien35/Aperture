# Open Design Decisions — AI Gateway & Spend Management Platform

These are implementation details the architecture diagrams imply but don't pin down numerically. Each one has a recommended default. If you disagree with a default, flag it in team chat before you start coding that piece — silence means the default is accepted and locked.

---

## 1. Cost Estimation Formula

**The question:** Before calling the provider, the gateway reserves an estimated cost in Redis. What formula produces that estimate?

**Default:**
```
estimated_cost = (prompt_tokens × input_price_per_token[model])
               + (max_tokens × output_price_per_token[model])
```
`prompt_tokens` can be counted client-side with a tokenizer (e.g. `tiktoken` for OpenAI-format requests) before the call is made. `max_tokens` is whatever the client requested, or the fallback below if unset.

**Open sub-question:** If the client doesn't set `max_tokens`, what ceiling do you reserve against?
- Option A: default to the model's max context window minus prompt length (safe, but can massively over-reserve and cause false-positive budget rejections)
- Option B: hardcode a conservative default like 4096 tokens (simpler, occasionally under-reserves)

**Recommendation:** Option B for the hackathon timeline. Document it as a known simplification.

---

## 2. Redis Fail-Open Grace Window

**The question:** If Redis (the budget-check hot path) becomes unreachable, does the gateway reject all requests immediately, or allow them through temporarily?

**Default:** Fail open for **10 seconds** from the first detected Redis failure, then fail closed (reject all requests) until Redis recovers. Track the "Redis has been down since T" timestamp in gateway process memory.

**Why not fail closed immediately:** A single Redis blip would take down the entire gateway for every user, even those nowhere near budget — bad availability for a product whose pitch is reliability.

**Why not fail open indefinitely:** Defeats the entire purpose of the budget enforcement feature (the PRD's core "runaway agent" scenario) if Redis has a real outage.

**Open sub-question:** If you run more than one gateway instance, is this 10-second window tracked per-instance (simple, may cause slightly inconsistent behavior across instances) or shared (needs its own coordination mechanism)?

**Recommendation:** Per-instance for the hackathon. You're likely running a single gateway instance anyway; document this as a scaling limitation.

---

## 3. Circuit Breaker Thresholds for Provider Fallback

**The question:** How aggressively does the gateway give up on the primary provider (Anthropic) and switch to the fallback (OpenAI)?

**Default:**
- **Trip to open (start failing over):** 3 consecutive failures (5xx errors or timeouts) from Anthropic.
- **Stay open for:** 30 seconds before attempting Anthropic again.
- **Half-open behavior:** after 30 seconds, allow exactly 1 test request through to Anthropic. If it succeeds, close the breaker (resume normal routing). If it fails, reopen for another 30 seconds.

**Why this matters:** Without a breaker, every single request during an Anthropic outage retries Anthropic first (adding latency) before falling back — the opposite of what a "reliability" feature should do.

---

## 4. Virtual Key Cache TTL and Revocation Lag

**The question:** Key metadata (budget limit, role, team) lives in DynamoDB but is read on every request — that's too slow/expensive to hit DynamoDB directly each time. How long is it cached in Redis?

**Default:** 60-second TTL on cached key metadata in Redis.

**Open sub-question:** Is it acceptable that a revoked key keeps working for up to 60 seconds after revocation?

**Recommendation:** Yes, accept this for the hackathon. State it explicitly in the README as a known limitation ("key revocation takes effect within 60 seconds") rather than building a cache-invalidation push mechanism, which is real added complexity for a demo-scale project.

---

## 5. Budget Reset Boundary

**The question:** Do daily/monthly budgets reset on a rolling window (e.g., "the last 24 hours from now") or a fixed calendar boundary (midnight UTC, 1st of the month)?

**Default:** Fixed calendar boundary — daily limits reset at 00:00 UTC, monthly limits reset on the 1st at 00:00 UTC.

**Why not rolling:** Rolling windows require a Redis sorted-set pattern with per-entry expiry and range queries, which is meaningfully more complex to implement correctly under concurrency. Fixed boundaries let you use a single counter key per period (e.g., `budget:{key_id}:2026-09-18`) that naturally "resets" simply by being a new key each day.

---

## 6. Partial-Stream Disconnects

**The question:** If a client disconnects mid-SSE-stream (closes their laptop, agent times out) before the response completes, what cost gets charged?

**Default:** Track a running token count as SSE chunks are forwarded to the client. On disconnect, reconcile the Redis reservation using tokens actually generated up to that point, not the full `max_tokens` estimate.

**Open sub-question:** If the provider's streaming API doesn't cleanly expose a partial token count on abrupt disconnect (implementation-dependent), what's the fallback?

**Recommendation:** If partial tracking proves too time-consuming to implement correctly, fall back to charging the full pre-reserved estimate on any abnormal disconnect, and document this as a known imprecision ("disconnected requests are charged at their full reserved estimate, not actual usage"). This is a safe-but-imprecise stopgap — it never under-charges, which protects the budget-enforcement guarantee, it just occasionally over-charges.

---

## 7. Kafka Delivery Guarantee vs. Gateway Availability

**The question:** Does publishing a usage event to Kafka ever block or slow down the response the client is waiting on?

**Default:** No. The producer uses `acks=1` (not `acks=all`) with a short send timeout (e.g., 500ms), and the publish call is wrapped in a try/except that logs and silently drops the event on failure. The gateway response to the client is never delayed by Kafka.

**Open sub-question:** Should dropped events (Kafka down, timeout) be buffered locally for retry, or just accepted as lost?

**Recommendation:** Accept as lost for the hackathon. A local retry buffer is a legitimate "Phase 2" feature but isn't worth the implementation time now — a small percentage of missing usage-log entries doesn't break the core demo (budget enforcement still works via Redis; only the historical dashboard would show a gap).

---

## 8. Idempotency Key for the Kafka Consumer

**The question:** Kafka guarantees at-least-once delivery, meaning the consumer can process the same message twice (on rebalance, crash before offset commit, etc.). If the consumer does a blind `ADD spend` on a DynamoDB aggregate item, a reprocessed message double-counts that spend.

**Default:** Every usage event carries a `request_id` generated at the *start* of the request (not at Kafka publish time, so retries share the same ID). The consumer performs a conditional write — write a `PROCESSED#<request_id>` marker item to DynamoDB with a condition expression `attribute_not_exists(PK)` — before applying the aggregate spend update. If the conditional write fails (marker already exists), skip the aggregate update; the message has already been processed.

**Why this matters:** This bug is invisible in a demo (numbers will look approximately right) and only surfaces as "the dashboard total looks a little too high" after real usage — expensive to debug later, cheap to prevent now.

---

## How to use this doc

Read through once as a team. For each decision, either:
- **Accept the default** (say nothing, or thumbs-up in chat), or
- **Flag disagreement** with your reasoning, before whoever's building that piece starts coding it.

Once accepted, treat these as locked for the sprint — revisit only if something breaks in testing, not mid-implementation on a hunch.
