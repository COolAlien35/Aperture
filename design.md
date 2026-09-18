# Aperture UI Design System — Portkey.ai Specification
**Version:** 1.0.0  
**Target Platform:** Aperture AI Gateway & Spend Management Platform (`dashboard/`)  
**Design Paradigm:** Exact Portkey.ai Enterprise Observability Theme (Deep Obsidian Charcoal, Electric Orange Accents, Neon Telemetry Indicators, Glassmorphic Paneling)

---

## 1. Design Philosophy & Aesthetic Blueprint

Portkey.ai is recognized for its high-performance, dark-mode developer UI built for AI infrastructure. The aesthetic combines:
- **Deep Obsidian Canvas (`#090A0D` / `#0E1015`)**: Deep, low-fatigue dark surfaces that make data visualization charts and telemetry metrics pop with crystal clarity.
- **Electric Portkey Orange (`#F97316` / `#FF5500`)**: The signature interactive brand accent used for primary CTAs, active states, active tab highlights, and spend metrics.
- **Glassmorphic Paneling & Micro-Borders (`#1E222D`)**: High-contrast, razor-thin 1px borders with subtle gradients that define structure without visual clutter.
- **Telemetry Indicators**: Cyberpunk-inspired status glows (`#10B981` Emerald for healthy/success, `#F59E0B` Amber for budget warnings, `#EF4444` Crimson for blocked/tripped breakers, `#06B6D4` Cyan for token consumption).
- **Dense, High-Information Tables**: Monospace typography for keys, timestamps, tokens, and dollar figures, paired with slide-out JSON inspection drawers.

---

## 2. Color Palette & Token System

### 2.1 Surfaces & Backgrounds
```css
:root {
  /* Canvas Backgrounds */
  --bg-app: #08090C;            /* Primary application canvas */
  --bg-sidebar: #0C0E12;        /* Fixed left navigation bar */
  --bg-header: rgba(12, 14, 18, 0.85); /* Glassmorphic top navigation */
  --bg-surface-1: #111318;      /* Primary card & widget surface */
  --bg-surface-2: #161920;      /* Elevated hover states & dropdowns */
  --bg-surface-3: #1C202A;      /* Modal, drawer & active item surface */
  --bg-surface-glass: rgba(20, 24, 33, 0.7); /* Translucent backdrop */

  /* Borders & Dividers */
  --border-subtle: #191C24;     /* Section dividers & subtle card borders */
  --border-default: #232733;    /* Standard element borders */
  --border-active: #323849;     /* Focused, selected, or hovered borders */
  --border-accent: rgba(249, 115, 22, 0.4); /* Glow border on focus/hover */
}
```

### 2.2 Brand & Telemetry Accents
```css
:root {
  /* Brand Signature (Portkey Orange) */
  --brand-primary: #F97316;     /* Primary brand color (Orange-500) */
  --brand-hover: #EA580C;       /* Button hover state (Orange-600) */
  --brand-subtle: rgba(249, 115, 22, 0.12); /* Badge background & pill highlight */
  --brand-glow: 0 0 20px rgba(249, 115, 22, 0.35); /* Card focus glow */

  /* Telemetry Status Colors */
  --status-success: #10B981;    /* 200 OK, Healthy Circuit, Active Key */
  --status-success-bg: rgba(16, 185, 129, 0.12);
  --status-success-border: rgba(16, 185, 129, 0.3);

  --status-warning: #F59E0B;    /* 80%+ Budget warning, Degrading upstream */
  --status-warning-bg: rgba(245, 158, 11, 0.12);
  --status-warning-border: rgba(245, 158, 11, 0.3);

  --status-danger: #EF4444;     /* Blocked requests, Over budget, Breaker OPEN */
  --status-danger-bg: rgba(239, 68, 68, 0.12);
  --status-danger-border: rgba(239, 68, 68, 0.3);

  --status-cyan: #06B6D4;       /* Tokens & Cache hits */
  --status-cyan-bg: rgba(6, 182, 212, 0.12);
  --status-purple: #8B5CF6;     /* Request counts & AI models */
  --status-purple-bg: rgba(139, 92, 246, 0.12);
}
```

### 2.3 Typography & Text Hierarchy
```css
:root {
  /* Font Families */
  --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif;
  --font-mono: 'JetBrains Mono', 'Fira Code', monospace;

  /* Text Colors */
  --text-primary: #F3F4F6;      /* High contrast titles & metrics (#F3F4F6) */
  --text-secondary: #9CA3AF;    /* Labels, descriptions, secondary copy */
  --text-muted: #6B7280;        /* Inactive states, table column headers */
  --text-dim: #4B5563;          /* Placeholder text, disabled items */
}
```

---

## 3. Visual Effects & Motion Specifications

1. **Backdrop Blur / Glassmorphism**:
   - `backdrop-filter: blur(16px) saturate(180%);` applied to top headers, floating filter pills, and slide-over drawers.
2. **Subtle Mesh Background**:
   - Radial ambient lighting in the top-right corner of the dashboard:
     `background: radial-gradient(circle at 85% -10%, rgba(249, 115, 22, 0.07) 0%, transparent 60%);`
3. **Live Pulse Indicators**:
   - 8px pulsing green ring next to **Kafka Broker**, **DynamoDB Connected**, and **Circuit Breaker: CLOSED**.
4. **Card Hover Lift**:
   - `transform: translateY(-2px); transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);`
   - Border transitions from `--border-default` to `--border-active` with subtle drop shadow `0 12px 28px rgba(0, 0, 0, 0.45)`.
5. **Chart Gradients**:
   - Area chart fills with vertical linear gradients fading from `rgba(249, 115, 22, 0.35)` at the peak down to `rgba(249, 115, 22, 0.0)` at zero.

---

## 4. UI Shell & Navigation Layout

```
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│ ✦ APERTURE [PORTKEY THEME]  │ 🏢 Team: Engineering ▾ │ 🟢 Gateway :8080 │ ⚡ Kafka :9092 │ 💾 DynamoDB :8001 │
├──────────────────┬─────────────────────────────────────────────────────────────────────────────────────────┤
│ 🧭 NAVIGATION    │ 📊 ANALYTICS OVERVIEW                                     [ Last 24h ▾ ] [ Refresh ⟳ ] │
│                  ├─────────────────────────────────────────────────────────────────────────────────────────┤
│ 📊 Overview      │ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────────┐ │
│ 📋 Request Logs  │ │ TOTAL SPEND  │ │ TOTAL TOKENS │ │ REQUESTS     │ │ AVG LATENCY  │ │ CIRCUIT STATE  │ │
│ 🔑 Virtual Keys  │ │ $12.35       │ │ 14,280       │ │ 62           │ │ 240 ms       │ │ CLOSED (Safe)  │ │
│ 🛡️ Budgets & RBAC│ │ +$0.0016 last│ │ 8.4k prompt  │ │ 57 ok / 5 blk│ │ p95: 410 ms  │ │ Anthropic Pri  │ │
│ ⚡ Fallbacks     │ └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ └────────────────┘ │
│ ⚙️ Configuration │ ┌──────────────────────────────────────────────────┐ ┌────────────────────────────────┐ │
│                  │ │ 📈 SPEND & REQUEST VOLUME (Time-Series)          │ │ 🍩 COST SHARE BY MODEL         │ │
│                  │ │ [Hourly Area Chart - Portkey Orange Gradient]    │ │ • Claude 3.5 Sonnet : 64% ($8) │ │
│                  │ │                                                  │ │ • GPT-4o            : 36% ($4) │ │
│                  │ └──────────────────────────────────────────────────┘ └────────────────────────────────┘ │
│                  │ ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
│                  │ │ 📋 LIVE USAGE TELEMETRY (Last 10 Events from DynamoDB)                              │ │
│                  │ │ [REQ ID]    [KEY ID]       [TEAM]    [MODEL]     [TOKENS]  [COST]  [STATUS]         │ │
│                  │ │ req-8f2a..  sk-gw-team..   engineer  claude-3-5  200       $0.0024 [ 200 OK ]       │ │
│                  │ │ req-31c0..  sk-gw-prod..   product   gpt-4o      140       $0.0018 [ 200 OK ]       │ │
│                  │ │ req-99ba..  sk-gw-dev01..  marketing gpt-4o      0         $0.0000 [ 403 BLOCKED ]  │ │
│                  │ └─────────────────────────────────────────────────────────────────────────────────────┘ │
└──────────────────┴─────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Screen Specifications & Features

### 5.1 Screen 1: Analytics Overview (`/`)
1. **Header Bar**:
   - App Logo: Aperture symbol with orange glow.
   - Live Connectivity Pills:
     - `Gateway: Healthy (HTTP 8080)`
     - `Kafka: Connected (aperture.usage-events)`
     - `DynamoDB: Active (aperture_data)`
   - Time Filter: Pill segmented controls (`24H`, `7D`, `30D`, `All Time`).
2. **Top Metric KPI Cards (5 Grid)**:
   - **Total Spend ($)**: Dynamic counter formatted with 4-decimal precision (`$12.3560`), month budget delta indicator.
   - **Total Tokens**: Formatted with SI suffix (`14.28k`), subtext showing `Prompt: 8.45k | Completion: 5.83k`.
   - **Request Volume**: Total requests, with sub-pills for `57 Successful` (Green) and `5 Blocked` (Red).
   - **Average Latency**: Mean duration in ms, subtext `P95: 380ms`.
   - **Fallback & Breaker**: `CLOSED` status badge with glowing pulse, showing 0 fallback triggers.
3. **Charts Grid**:
   - **Main Telemetry Chart**: Dual-axis or toggleable Area Chart showing **Hourly Spend ($)** and **Request Count**. Portkey Orange gradient fill with tooltip inspection.
   - **Model Cost Breakdown**: Donut chart with center total spend, detailing dollar and percentage distribution per model (`claude-sonnet-4-6`, `gpt-4o`, `gpt-4o-mini`).
   - **Team Spend Gauges**: Horizontal progress bars showing current spend against budget limits (e.g., Engineering: `$8.40 / $100.00` = 8.4%, Product: `$3.95 / $50.00` = 7.9%).
4. **Recent Activity Feed**:
   - Real-time rolling table showing the latest 10 requests from DynamoDB with instant status badges.

---

### 5.2 Screen 2: Live Observability & Request Logs (`/logs`)
1. **Search & Filter Controls**:
   - Search bar (by `request_id`, `key_id`, or `model`).
   - Dropdown filters: Team (`All`, `Engineering`, `Product`), Status (`All`, `200 Success`, `403 Blocked`).
2. **Dense Data Table**:
   - Columns:
     - `Status`: Green pill (`200 OK`) or Red pill (`BLOCKED`).
     - `Timestamp`: Formatted relative time (`2 mins ago`) + ISO hover tooltip.
     - `Request ID`: Monospace badge with 1-click copy button (`req-8f2...`).
     - `Virtual Key`: Key badge (`sk-gw-eng...`).
     - `Team`: Team name chip.
     - `Model`: Provider model badge (`claude-sonnet-4-6` with Anthropic icon, `gpt-4o` with OpenAI icon).
     - `Tokens`: Total tokens with prompt/completion breakdown tooltip.
     - `Cost`: Monetary value in `$0.0000` format.
3. **Slide-Out Details Drawer (Portkey Style)**:
   - Clicking any row slides out a right-hand inspection drawer:
     - Top bar with Request ID, Status code, Latency, and Timestamp.
     - Formatted tabs: **Overview**, **Cost Breakdown** (Prompt Cost + Completion Cost calculation), and **Raw DynamoDB Item (JSON)**.

---

### 5.3 Screen 3: Virtual Keys & RBAC (`/keys`)
1. **Action Bar**:
   - `+ Create Virtual Key` button (opens modal).
2. **Virtual Keys Table** (Direct representation of DynamoDB `KEY#<id> / METADATA`):
   - `Key Name` & `Virtual Key ID` (`sk-gw-...`).
   - `Team`: (`engineering`, `product`, `marketing`).
   - `Role`: Pill badge (`Admin` - Purple, `Team Lead` - Blue, `Developer` - Gray).
   - `Budget Limit`: Monthly USD limit (`$100.00`).
   - `Status`: Toggle switch for `Active` / `Revoked`.
   - `Actions`: Copy Key, Edit Limit, Revoke Key.
3. **Create Key Modal**:
   - Form fields: Name, Team, Role dropdown, Monthly Budget Limit input.

---

### 5.4 Screen 4: Team Budgets & Kill-Switches (`/budgets`)
1. **Overview Cards**:
   - Total Allocated Budget vs. Total Organization Spend.
   - Kill-Switch Alert Banner: Shows how many requests were blocked at the gateway before hitting LLM APIs.
2. **Team Budget Cards**:
   - Card for each team (`Engineering`, `Product`, `Marketing`):
     - Team Name & Active Key Count.
     - Large Spend Counter: `$8.40` spent of `$100.00` monthly limit.
     - Animated progress bar (Color transitions: Emerald < 80%, Amber 80-99%, Crimson >= 100%).
     - Blocked Requests counter (shows money saved from runaway loops).
     - Quick Edit Budget Limit action.

---

### 5.5 Screen 5: Gateway Routing & Circuit Breakers (`/gateway`)
1. **Visual Pipeline Diagram**:
   - Client (`Cursor / SDK`) ➔ `Aperture Gateway (:8080)` ➔ `Circuit Breaker` ➔ `Primary (Anthropic)` OR `Fallback (OpenAI)`.
2. **Circuit Breaker Live Telemetry**:
   - State: `CLOSED` (Normal), `OPEN` (Tripped), `HALF-OPEN` (Probing).
   - Failure Threshold: 3 consecutive 5xx errors.
   - Recovery Window: 60 seconds probe timer.
   - Failure Count: `0 / 3`.
   - Manual Simulator: "Trigger Test Failure" button to demonstrate automated fallback to OpenAI.

---

## 6. DynamoDB Data Binding Matrix (Person C Contract)

| UI Element / Widget | DynamoDB Item / Index Query | Attributes Used |
| :--- | :--- | :--- |
| **Top KPI: Monthly Spend** | `PK = TEAM#<id>, SK = SPEND#<YYYY-MM>` | `total_spend_usd` (Decimal sum across teams) |
| **Top KPI: Total Tokens** | `PK = TEAM#<id>, SK = SPEND#<YYYY-MM>` | `total_tokens` (Summed across teams) |
| **Top KPI: Total Requests** | `PK = TEAM#<id>, SK = SPEND#<YYYY-MM>` | `total_requests`, `requests_blocked` |
| **Live Request Logs** | `PK = KEY#<id>, SK begins_with USAGE#` OR `GSI1PK = <team>, GSI1SK begins_with USAGE#` | `request_id`, `model`, `prompt_tokens`, `completion_tokens`, `total_tokens`, `actual_cost_usd`, `status`, `timestamp` |
| **Team Budget Progress** | `PK = TEAM#<id>, SK = SPEND#<YYYY-MM>` | `total_spend_usd`, `month`, `requests_blocked` |
| **Virtual Keys List** | `GSI1SK = METADATA` (Query GSI1) | `key_id`, `name`, `team_id`, `role`, `budget_limit`, `is_active`, `created_at` |
| **Idempotency Proof** | `PK = PROCESSED#<req_id>, SK = MARKER` | `TTL`, `processed_at` |

---

## 7. Component File Structure (`dashboard/`)

```
dashboard/
├── index.html                   # HTML entry with Google Fonts (Plus Jakarta Sans, JetBrains Mono)
├── package.json                 # React 18, Vite, Lucide Icons, Recharts
├── vite.config.js               # Dev server proxying /api to Gateway
├── src/
│   ├── index.css                # Portkey design tokens, Tailwind / CSS variables, scrollbars
│   ├── App.jsx                  # Main shell: Header, Sidebar, Routing
│   ├── components/
│   │   ├── Header.jsx           # Live service pills, org switcher, time selector
│   │   ├── Sidebar.jsx          # Portkey nav icons, active indicator
│   │   ├── MetricCard.jsx       # Standardized KPI widget with sparkline/delta
│   │   ├── StatusBadge.jsx      # Telemetry pill badges (200 OK, Blocked, etc.)
│   │   ├── SlideDrawer.jsx      # Right slide-over JSON request inspector
│   │   └── Modal.jsx            # Create key / edit budget dialogs
│   ├── views/
│   │   ├── OverviewView.jsx     # Main KPI cards, charts, recent stream
│   │   ├── LogsView.jsx         # Full-screen filterable request logs table
│   │   ├── KeysView.jsx         # Virtual keys management & creation
│   │   ├── BudgetsView.jsx      # Team budgets, progress gauges, kill-switch logs
│   │   └── GatewayView.jsx      # Circuit breaker health & fallback topology
│   └── services/
│       ├── api.js               # Gateway & DynamoDB query client
│       └── mockData.js          # Realistic seed fallback data for instant preview
```

---

## 8. Implementation Milestones

1. **Phase 1: Design Tokens & Foundations**
   - Configure Vite React project in `dashboard/`.
   - Setup `index.css` with exact Portkey color variables, borders, glassmorphic effects, and typography.
2. **Phase 2: App Shell & Navigation**
   - Implement `Sidebar` and `Header` with live status indicators for Gateway (`:8080`), Kafka (`:9092`), and DynamoDB (`:8001`).
3. **Phase 3: Views Implementation**
   - Build `OverviewView`: KPI cards, Recharts time-series spend chart, model donut, team progress gauges.
   - Build `LogsView`: Searchable table with slide-out details drawer.
   - Build `KeysView`: Virtual keys table with RBAC badges and creation modal.
   - Build `BudgetsView`: Team budget cards with threshold color shifts.
   - Build `GatewayView`: Visual circuit breaker diagram with live status.
4. **Phase 4: API Integration & Live Data**
   - Connect frontend to Gateway and DynamoDB Local to render real live usage data.
