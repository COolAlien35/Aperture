# Aperture — Unified DynamoDB Single-Table Schema & Coordination Contract

**Document Version:** 2.0 (Phase 2 Finalized Contract)  
**Owners:** Person C (Data Layer & Schema Owner), Person A (Git Activity & Session Correlation), Person B (Budgets & Forecasting)  
**Target Table Name:** `aperture_data` (Partition Key: `PK`, Sort Key: `SK`)

---

## 1. Executive Summary & Design Principles

Aperture uses an **overloaded single-table DynamoDB design** to support high-throughput telemetry writes, idempotent event processing, and low-latency financial queries.

### Guiding Principles
1. **Zero Contention Hot Paths:** Read and write patterns partition high-velocity telemetry (per-request usage) away from team aggregates.
2. **Idempotency Guarantee:** At-least-once Kafka message delivery is deduplicated via a conditional put on `PROCESSED#<request_id>` before applying atomic updates.
3. **Additive Schema Evolution:** New fields (such as `session_id`) extend existing items without altering partition keys or breaking existing readers.

---

## 2. Table Index Definitions

| Index Name | Partition Key (`PK`) | Sort Key (`SK`) | Projection | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Base Table** | `PK` (String) | `SK` (String) | `ALL` | Core single-table access pattern |
| **GSI1 (Team Usage)** | `GSI1PK` (String) | `GSI1SK` (String) | `ALL` | Query team usage logs across all virtual keys chronologically |
| **GSI2 (Requests Status)**| `status` (String) | `timestamp` (String)| `KEYS_ONLY` | Filter pending budget requests & anomalous 403 blocks |

---

## 3. Entity Specifications & Key Patterns

### Entity 1: Idempotency Marker (Person C)
- **Purpose:** Deduplicate Kafka delivery replays.
- **PK:** `PROCESSED#<request_id>`
- **SK:** `MARKER`
- **Attributes:**
  - `request_id` (String)
  - `processed_at` (String, ISO 8601 UTC)
  - `TTL` (Number, Unix epoch timestamp = now + 30 days)
- **Condition Expression:** `attribute_not_exists(PK)`

### Entity 2: Raw Request Usage Log (Person C + Person A)
- **Purpose:** Full audit log of all model calls, token costs, latency, and session linkage.
- **PK:** `KEY#<key_id>`
- **SK:** `USAGE#<timestamp>`
- **GSI1PK:** `<team_id>`
- **GSI1SK:** `USAGE#<timestamp>`
- **Attributes:**
  - `request_id` (String)
  - `key_id` (String)
  - `team_id` (String)
  - `model` (String, e.g. `claude-3-5-sonnet`)
  - `prompt_tokens` (Number)
  - `completion_tokens` (Number)
  - `total_tokens` (Number)
  - `actual_cost_usd` (Number / Decimal)
  - `estimated_cost_usd` (Number / Decimal)
  - `status` (String: `success` | `error` | `blocked` | `partial`)
  - `timestamp` (String, ISO 8601 UTC)
  - `session_id` *(NEW — Phase 2)*: Optional client or Claude Code session identifier (String, e.g. `sess_abc123`)
  - `error_message` (String, optional)

### Entity 3: Team Monthly Spend Aggregate (Person C + Person B)
- **Purpose:** Fast atomic counter for team budgets and monthly spend.
- **PK:** `TEAM#<team_id>`
- **SK:** `SPEND#<YYYY-MM>`
- **Attributes:**
  - `team_id` (String)
  - `month` (String, `YYYY-MM`)
  - `total_spend_usd` (Atomic `ADD` Decimal)
  - `total_requests` (Atomic `ADD` Number)
  - `total_tokens` (Atomic `ADD` Number)
  - `requests_blocked` (Atomic `ADD` Number)
  - `last_updated` (String, ISO 8601 UTC)

### Entity 4: Git Activity & PR Correlation (Person A)
- **Purpose:** Track git commits, pull requests, and correlated AI spend per outcome.
- **PK:** `REPO#<repo_id>` (e.g. `REPO#org/backend-repo`)
- **SK Options:**
  - For Pull Requests: `PR#<pr_number>` (e.g. `PR#142`)
  - For Commits: `COMMIT#<timestamp>` (e.g. `COMMIT#2026-09-19T14:22:00Z`)
- **Attributes for PRs (`PR#<pr_number>`):**
  - `repo_id` (String)
  - `pr_number` (Number)
  - `pr_title` (String, e.g. *"feat: add semantic caching layer"*)
  - `pr_url` (String, clickable GitHub/GitLab URL)
  - `author` (String, GitHub handle)
  - `created_at` (String, ISO 8601)
  - `merged_at` (String, ISO 8601, nullable)
  - `time_to_merge_hours` (Number)
  - `files_changed` (Number)
  - `session_ids` (List of Strings, mapped to usage events)
  - `total_ai_cost_usd` (Decimal, aggregated correlated spend)
  - `attribution_confidence` (String: `high` | `medium` | `estimated`)

### Entity 5: Budget Requests & Approvals (Person B)
- **Purpose:** Workflow queue for requesting and approving departmental budget changes.
- **PK:** `TEAM#<team_id>`
- **SK:** `REQUEST#<timestamp>` (e.g. `REQUEST#2026-09-19T17:30:00Z`)
- **Attributes:**
  - `request_id` (String, UUID)
  - `team_id` (String)
  - `requested_by` (String, e.g. `dev@aperture.io`)
  - `current_budget_usd` (Decimal)
  - `requested_budget_usd` (Decimal)
  - `reason` (String, required business justification)
  - `status` (String: `pending` | `approved` | `denied`)
  - `reviewed_by` (String, nullable)
  - `reviewed_at` (String, ISO 8601, nullable)
  - `rejection_reason` (String, optional)

---

## 4. Endpoints & Query Access Patterns

| Pattern | Target | Key Condition | Output |
| :--- | :--- | :--- | :--- |
| **Get Team Usage** | GSI1 | `GSI1PK = :team_id AND GSI1SK BEGINS_WITH USAGE#` | Audit stream for team |
| **Get PR Cost Attribution** | Base | `PK = REPO#<repo_id> AND SK BEGINS_WITH PR#` | Ranked PR cost table |
| **Get Pending Budget Requests**| Base | `PK = TEAM#<team_id> AND SK BEGINS_WITH REQUEST#` | Approval queue |
| **Get Monthly Spend** | Base | `PK = TEAM#<team_id> AND SK = SPEND#<YYYY-MM>` | Live quota vs spend |

---

## 5. Person A & B Coordination Sign-off

- [x] **Person A Contract Confirmed:** `PK: REPO#<repo_id>, SK: PR#<pr_number>` with `session_ids` linkage to `UsageEvent.session_id`.
- [x] **Person B Contract Confirmed:** `PK: TEAM#<team_id>, SK: REQUEST#<timestamp>` with mandatory `reason` string and atomic updates to `current_budget_usd`.
- [x] **Person C Contract Confirmed:** `session_id` added to `UsageEvent` model and consumer handler; `PROCESSED#<request_id>` deduplication preserved with zero regressions.
