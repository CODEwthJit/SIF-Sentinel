# Phase 9.1 — FastAPI Backend Architecture & API Specification

**Project**: SIH26165 — AI/NLP Engine for Serious Injury & Fatality (SIF) Precursor Analysis  
**Module**: `backend/`  
**Framework**: FastAPI, Pydantic v2, SQLAlchemy 2.0, PostgreSQL / SQLite  
**Phase**: Phase 9.1 (Production Backend API)  
**Status**: COMPLETE & VERIFIED  

---

## 1. Overview & Architectural Principles

The Phase 9.1 backend introduces a production-style REST API layer surrounding the **frozen intelligence core** developed in Phases 5–7. 

### Core Architectural Invariants:
1. **Frozen Intelligence Decoupling**:
   - The API layer executes **zero ML inference logic** and **zero rule evaluations** directly.
   - All analysis delegates strictly through the canonical pipeline entrypoint: `src.sif_pipeline.analyze_report(narrative)`.
2. **Metadata Quarantine Enforcement**:
   - The API strictly accepts only the incident narrative string (`ReportCreate.narrative`).
   - Outcome fields (`fatal`, `hospitalized`, `amputation`, etc.) are completely prohibited from request payloads and database models.
3. **Clean Service Layer Pattern**:
   - FastAPI routes contain **zero business logic**.
   - Database transactions, pipeline execution, and schema mappings are encapsulated in `AnalysisService`.
4. **Relational Data Persistence**:
   - Manages application state, report audit histories, and real-time dashboard analytics via PostgreSQL (with SQLite zero-config local development support).

---

## 2. System Architecture

```
HTTP Client (Frontend / Integration)
                │
                ▼
        FastAPI Router
  (api/v1/health, reports, dashboard)
                │
                ▼
         Service Layer
   (services/analysis_service.py)
                │
        ┌───────┴───────────────────────┐
        ▼                               ▼
 Frozen SIF Pipeline             SQLAlchemy ORM
 (src/sif_pipeline.py)            (db/models.py)
   ├── Frozen ML (tau=0.59)             ├── reports
   ├── Frozen Rule V2.3                 ├── analyses
   └── SIF Reconciliation               └── users
        │                               │
        └───────────────┬───────────────┘
                        ▼
            Typed Pydantic Schemas
              (schemas/analysis.py)
                        │
                        ▼
               JSON HTTP Response
```

---

## 3. Database Schema

The relational database is configured via SQLAlchemy 2.0:

### `reports` Table
Stores primary incident records submitted by users:
- `id` (Integer, Primary Key, Autoincrement)
- `narrative` (Text, Nullable=False)
- `created_at` (DateTime with Timezone, Server Default=now())

### `analyses` Table
Stores immutable results from each pipeline evaluation linked to a report:
- `id` (Integer, Primary Key, Autoincrement)
- `report_id` (Integer, Foreign Key `reports.id` ON DELETE CASCADE, Indexed)
- `ml_label` (String(20), Nullable=False) — `"YES"` or `"NO"`
- `ml_score` (Float, Nullable=False) — Model-estimated propensity for YES precursor class
- `ml_threshold` (Float, Nullable=False) — Locked threshold ($0.59$)
- `decision_rationale` (Text, Nullable=True)
- `positive_evidence` (JSON, Nullable=True) — List of positive lexical tokens ($w_j \cdot x_j$)
- `negative_evidence` (JSON, Nullable=True) — List of mitigating lexical tokens ($w_j \cdot x_j$)
- `rule_label` (String(20), Nullable=False) — `"YES"`, `"NO"`, or `"UNCERTAIN"`
- `rule_reason_code` (String(100), Nullable=True) — e.g. `GRAVITATIONAL_EXPOSURE`
- `rule_energy` (String(100), Nullable=True) — e.g. `GRAVITATIONAL`
- `rule_barrier` (String(100), Nullable=True) — e.g. `DAMAGED_OR_MISSING`
- `rule_exposure` (String(100), Nullable=True) — e.g. `DIRECT`
- `rule_evidence_sufficiency` (String(50), Nullable=True) — e.g. `STRONG`
- `precursor_type` (String(100), Nullable=True)
- `confidence` (String(50), Nullable=True)
- `reconciliation_status` (String(50), Nullable=False, Indexed) — e.g. `CONSENSUS_SIF`
- `reconciliation_priority` (String(20), Nullable=False, Indexed) — `HIGH`, `MEDIUM`, or `LOW`
- `human_review_required` (Boolean, Nullable=False, Indexed)
- `discrepancy` (Boolean, Nullable=False)
- `explanation` (Text, Nullable=True) — Audit rationale
- `created_at` (DateTime with Timezone, Server Default=now())

### `users` Table
Foundation for authentication and user attribution:
- `id` (Integer, Primary Key, Autoincrement)
- `email` (String(255), Unique, Indexed, Nullable=False)
- `username` (String(100), Unique, Indexed, Nullable=False)
- `is_active` (Boolean, Default=True, Nullable=False)
- `created_at` (DateTime with Timezone, Server Default=now())

---

## 4. REST API Endpoints

### Health Check
- **`GET /api/v1/health`**
  - **Description**: Returns live service health, engine specifications, and active baseline.
  - **Response 200**:
    ```json
    {
      "status": "ok",
      "service": "SIH26165 — SIF Precursor Detection API",
      "version": "1.0.0",
      "pipeline": "2.3.0-BUGFIX-FROZEN",
      "ml_model": "TF-IDF + Logistic Regression (tau=0.59)",
      "reconciliation": "Categorical Matrix Triage"
    }
    ```

### Report Analysis & History
- **`POST /api/v1/reports/analyze`**
  - **Description**: Submits an incident narrative for end-to-end SIF analysis and persists results.
  - **Request Body**:
    ```json
    {
      "narrative": "An employee fell 28 feet from a scaffold after the scaffold collapsed."
    }
    ```
  - **Response 201**:
    ```json
    {
      "report": {
        "id": 1,
        "narrative": "An employee fell 28 feet from a scaffold after the scaffold collapsed.",
        "created_at": "2026-09-13T11:36:47.123456Z"
      },
      "ml": {
        "label": "YES",
        "score": 0.9966,
        "threshold": 0.59,
        "positive_evidence": [
          {"feature": "fell", "contribution": 1.48},
          {"feature": "scaffold", "contribution": 1.12}
        ],
        "negative_evidence": [],
        "decision_rationale": "Score 0.9966 >= threshold 0.59."
      },
      "rule": {
        "label": "YES",
        "reason_code": "GRAVITATIONAL_EXPOSURE",
        "controlling_hazard_energy": "GRAVITATIONAL",
        "barrier_state": "DAMAGED_OR_MISSING",
        "human_exposure": "DIRECT",
        "evidence_sufficiency": "STRONG",
        "precursor_type": "HIGH_ENERGY_FATAL_COLLAPSE",
        "confidence": "HIGH"
      },
      "reconciliation": {
        "status": "CONSENSUS_SIF",
        "priority": "HIGH",
        "discrepancy": false,
        "review_required": false,
        "explanation": "Full Consensus SIF Precursor: ML predicts YES (score=0.9966) and V2.3 rule engine predicts YES (energy=GRAVITATIONAL, reason=GRAVITATIONAL_EXPOSURE). High-confidence precursor candidate."
      }
    }
    ```
  - **Error 422**: When narrative is empty or missing.

- **`GET /api/v1/reports`**
  - **Description**: Retrieves paginated historical incident reports ordered by recency.
  - **Query Params**: `limit` (default: 20), `offset` (default: 0).
  - **Response 200**: Array of `ReportOut` objects.

- **`GET /api/v1/reports/{report_id}`**
  - **Description**: Retrieves full report detail with its latest SIF analysis breakdown.
  - **Response 200**: `ReportDetailResponse` object.
  - **Error 404**: When `report_id` does not exist.

### Dashboard Analytics
- **`GET /api/v1/dashboard/stats`**
  - **Description**: Returns live aggregate statistics computed strictly from persisted analyses.
  - **Response 200**:
    ```json
    {
      "total_reports": 147,
      "total_analyses": 147,
      "consensus_sif_count": 116,
      "consensus_non_sif_count": 26,
      "discrepancy_count": 5,
      "high_priority_count": 121,
      "medium_priority_count": 0,
      "low_priority_count": 26,
      "reconciliation_status_distribution": {
        "CONSENSUS_SIF": 116,
        "CONSENSUS_NON_SIF": 26,
        "DIRECT_DISAGREEMENT": 5
      },
      "review_priority_distribution": {
        "HIGH": 121,
        "LOW": 26
      },
      "rule_reason_code_distribution": {
        "GRAVITATIONAL_EXPOSURE": 65,
        "ELECTRICAL_CONTACT": 28
      },
      "hazard_energy_distribution": {
        "GRAVITATIONAL": 65,
        "ELECTRICAL": 28
      }
    }
    ```

- **`GET /api/v1/dashboard/recent`**
  - **Description**: Returns recent analysis activity items for live frontend feeds.
  - **Query Params**: `limit` (default: 10).
  - **Response 200**: `DashboardRecentResponse` object.

---

## 5. Environment Configuration

Configuration is loaded from environment variables in `backend/app/core/config.py`:

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `DATABASE_URL` | `sqlite:///./sif_backend.db` | Connection string for PostgreSQL (or SQLite local fallback). |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173,...` | Comma-separated allowed frontend origins. |
| `ENVIRONMENT` | `development` | Runtime environment name. |

To configure PostgreSQL:
```bash
# In .env:
DATABASE_URL=postgresql://postgres:password@localhost:5432/sif_production
```

---

## 6. Local Development Commands

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch FastAPI Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```

- **Interactive Swagger Documentation**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`

---

## 7. Testing & Verification

Automated tests are located in `backend/tests/`:
- `test_health.py`: Verifies `/health` and root endpoints.
- `test_reports.py`: Tests empty narrative rejection, pipeline execution, persistence, failure handling, history, and detail.
- `test_dashboard.py`: Tests empty and populated statistics aggregation, and recent analysis feeds.

### Run Tests:
```bash
# Run backend tests only
pytest backend/tests -v

# Run complete project test suite (existing + backend)
pytest
```

**Test Suite Verification Results**:
- **Existing Frozen Tests**: `346 passed`
- **New Backend Tests**: `11 passed`
- **Total Project Tests**: `357 passed (100.0%)`

