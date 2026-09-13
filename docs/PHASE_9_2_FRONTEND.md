# Phase 9.2 — React / TypeScript Frontend Platform Specification

**Project**: SIH26165 — AI/NLP Engine for Serious Injury & Fatality (SIF) Precursor Analysis  
**Module**: `frontend/`  
**Technology Stack**: React 18, Vite 5, TypeScript 5, Tailwind CSS 3, React Router 6, Recharts 2, Axios  
**Phase**: Phase 9.2 (Production Demonstration Frontend)  
**Status**: COMPLETE & VERIFIED  

---

## 1. Overview & UI Philosophy

The **SIH26165 Frontend Application** is a production-grade, portfolio-ready Environmental Health & Safety (EHS) intelligence dashboard built to interact with the Phase 9.1 FastAPI backend.

### Core Design Principles:
1. **Zero Client-Side Classification Logic**:
   - The frontend acts strictly as a visual presentation layer.
   - All statistical inference, energy deduction, and categorical reconciliation are performed by the frozen backend intelligence pipeline (`/api/v1/reports/analyze`).
2. **Metadata Quarantine Preserved**:
   - Accepts exclusively the incident narrative string.
   - No input controls exist for outcome severity (`fatal`, `hospitalized`, `amputation`).
3. **Industrial EHS Aesthetics**:
   - Designed with clean, professional typography, crisp card containers, accessible status badges, restrained color-coding, and informative data visualizations.
   - Strictly eliminates gimmicky animations, excessive glassmorphism, or ungrounded claims.
4. **Mandatory Scientific Language**:
   - The ML score is explicitly labeled as **"Model-estimated SIF precursor propensity"** rather than "probability of injury or death".
   - Independent evidence disagreements trigger active visual circuit-breaker notices (*"Independent evidence channels disagree. Qualified safety review is required."*).

---

## 2. Architecture & File Structure

```
frontend/
├── index.html                   # HTML entrypoint with Inter font integration
├── package.json                 # Dependencies and npm scripts
├── tsconfig.json                # TypeScript compiler configuration
├── vite.config.ts               # Vite bundler & proxy configuration
├── tailwind.config.js           # Tailwind CSS configuration with industrial palette
├── .env.example                 # Environment template (VITE_API_BASE_URL)
└── src/
    ├── main.tsx                 # React DOM mount point
    ├── App.tsx                  # React Router root definition
    ├── index.css                # Tailwind base styles
    ├── types/
    │   └── api.ts               # Typed contracts mirroring FastAPI Pydantic schemas
    ├── services/
    │   ├── api.ts               # Axios client with centralized error interception
    │   ├── reportService.ts     # Analysis and history query client
    │   └── dashboardService.ts  # Analytics metrics and health probe client
    ├── components/
    │   ├── Sidebar.tsx          # Navigation sidebar with frozen engine badges
    │   ├── StatCard.tsx         # KPI metric cards with status icons
    │   ├── StatusBadge.tsx      # Color-coded categorical triage badges
    │   ├── PriorityBadge.tsx    # High/Medium/Low priority badges
    │   ├── MLEvidenceCard.tsx   # Statistical propensity & lexical token weights (w_j · x_j)
    │   ├── RuleEvidenceCard.tsx # Physical energy, reason code, and barrier deductions
    │   ├── ReconciliationCard.tsx # Triage status, flags, and circuit-breaker alerts
    │   ├── LoadingState.tsx     # Clean loading indicator
    │   ├── ErrorState.tsx       # Alert banner with retry trigger
    │   └── EmptyState.tsx       # Empty state placeholder
    ├── layouts/
    │   └── RootLayout.tsx       # Top operational header, sidebar, and governance footer
    ├── pages/
    │   ├── Dashboard.tsx        # KPI metrics, recent triage feed, and Recharts charts
    │   ├── Analyze.tsx          # Narrative input, benchmark presets, dual evidence cards
    │   ├── History.tsx          # Paginated log with live keyword search
    │   └── ReportDetail.tsx     # Full audit trail for specific incident reports
    └── test/
        ├── setup.ts             # Vitest test setup with ResizeObserver polyfill
        ├── Dashboard.test.tsx   # Dashboard KPI and feed render tests
        ├── Analyze.test.tsx     # Form validation and API response tests
        ├── History.test.tsx     # Report listing and search filter tests
        └── ReportDetail.test.tsx# Detailed report audit render tests
```

---

## 3. Application Routes

| Path | Component | Description |
| :--- | :--- | :--- |
| **`/`** | Redirect | Automatically redirects to `/dashboard`. |
| **`/dashboard`** | `Dashboard.tsx` | High-level KPI cards, recent analyses table, and distributions for status, priority, reason code, and hazard energy. |
| **`/analyze`** | `Analyze.tsx` | Incident narrative text area with benchmark incident presets and real-time dual-channel evidence display. |
| **`/history`** | `History.tsx` | Paginated chronological table of submitted incident reports with client-side keyword filtering. |
| **`/reports/:id`** | `ReportDetail.tsx`| In-depth audit view displaying the raw incident narrative, ML propensity attribution, and rule energy deductions. |

---

## 4. Benchmark Incident Presets (in Analyze Page)

The Analyze page includes quick-load buttons for 5 authentic industrial benchmark incidents:
1. **Scaffold Fall**: High-elevation fall $\to$ `CONSENSUS_SIF` (HIGH priority).
2. **Sidewalk Ice Slip**: Low-energy flat ground slip $\to$ `CONSENSUS_NON_SIF` (LOW priority).
3. **Conference Room Medical**: Routine non-industrial cardiac event $\to$ `CONSENSUS_NON_SIF` (LOW priority).
4. **Conveyor Tool Jam**: Hand tool trapped in running conveyor $\to$ `DIRECT_DISAGREEMENT` (HIGH priority audit circuit-breaker).
5. **Ambiguous Operation**: Brief report lacking energy context $\to$ `RULE_UNCERTAIN_ML_SIGNAL` (HIGH priority audit).

---

## 5. Environment Configuration

Configuration is managed via Vite environment variables:
```bash
# In frontend/.env:
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

If not provided, the API client defaults to `http://127.0.0.1:8000/api/v1` or proxies through Vite dev server `/api/v1`.

---

## 6. How to Run & Build the Frontend

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Start Development Server
```bash
npm run dev
```
Open your browser at `http://127.0.0.1:5173`.

### 3. Production Build
```bash
npm run build
```
Generates optimized static assets in `frontend/dist/`.

---

## 7. Testing & Verification

Automated frontend testing is implemented using **Vitest** and **React Testing Library**:
```bash
cd frontend
npm run test
```

### Frontend Test Results:
- **`Dashboard.test.tsx`**: Verified initial loading state, KPI cards, recent analysis table, and connection error handling (3 tests).
- **`Analyze.test.tsx`**: Verified input controls, client-side empty narrative validation, complete dual-channel evidence rendering, and API failure alerts (4 tests).
- **`History.test.tsx`**: Verified report listing from API and real-time narrative search filtering (2 tests).
- **`ReportDetail.test.tsx`**: Verified comprehensive audit trail rendering and 404 error handling (2 tests).

**Total Frontend Tests**: `11 passed (100%)`.  
**Total Existing Backend & Engine Tests**: `357 passed (100%)`.  
**Combined Project Test Suite**: `368 passed (100%)`.

