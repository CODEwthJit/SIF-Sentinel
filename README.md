# SIF Sentinel — AI-Powered Safety Intelligence

An industrial-grade, local-first full-stack AI platform for detecting **Serious Injury & Fatality (SIF) Precursors** from unstructured workplace incident narratives.

SIF Sentinel combines statistical machine learning with deterministic energy-precedence physics rules in a dual-channel architecture, resolving disagreements via a categorical reconciliation engine to gate high-risk incidents for human safety expert review.

*(Developed as a production-oriented full-stack portfolio application).*

---

## Quick Start (Single-Command Launch)

Run one command from the repository root to automatically verify prerequisites, check dependencies, launch both backend and frontend servers, and open the application in your browser:

### Windows:
```cmd
run.bat
```
*(Or simply double-click `run.bat` in Windows Explorer)*

### macOS / Linux:
```bash
chmod +x run.sh
./run.sh
```

### Universal (Any OS with Python 3.10+ and Node.js):
```bash
python run.py
```

### What happens automatically:
1. **Prerequisite Validation**: Verifies Python 3.10+ and Node.js/npm are available on the system.
2. **Port Conflict Protection**: Ensures ports `8000` (FastAPI) and `5173` (Vite) are free from stale processes.
3. **Dependency Check & Auto-Install**: Audits Python packages and frontend `node_modules`, installing missing packages as needed.
4. **Dual Server Launch**: Concurrently boots the FastAPI backend and Vite React frontend.
5. **Health Readiness Probing**: Polls endpoints until both services return HTTP 200.
6. **Automated Browser Launch**: Opens your default browser directly to `http://localhost:5173/login`.
7. **Clean Graceful Shutdown**: Press **`Ctrl+C`** (Windows/Linux) or **`Cmd+C`** (macOS) in your terminal at any time to immediately terminate all processes and free all ports without leaving background tasks.

---

## Application URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | `http://localhost:5173` | React + TypeScript + Tailwind UI |
| **Login / Register** | `http://localhost:5173/login` | Authentication entrypoint |
| **Backend REST API** | `http://127.0.0.1:8000` | FastAPI service |
| **Interactive API Docs** | `http://127.0.0.1:8000/docs` | Swagger / OpenAPI Explorer |

---

## System Architecture

```
                       Unstructured Safety Narrative
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
            ┌───────────────────────┐   ┌───────────────────────┐
            │   Machine Learning    │   │ Deterministic Rules   │
            │  TF-IDF + LogReg      │   │  V2.3 Energy Engine   │
            │  (Threshold τ = 0.59) │   │  (Physical Energies)  │
            └───────────┬───────────┘   └───────────┬───────────┘
                        │                           │
                        │    ML Score & Tokens      │    Energy & Barrier Code
                        └───────────┬───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │  SIF Reconciliation Engine    │
                    │  (Categorical Triage Matrix)  │
                    └───────────────┬───────────────┘
                                    ▼
                    ┌───────────────────────────────┐
                    │      Auditable Triage:        │
                    │   • CONSENSUS_SIF             │
                    │   • CONSENSUS_NON_SIF         │
                    │   • HUMAN REVIEW REQUIRED     │
                    └───────────────┬───────────────┘
                                    ▼
                    FastAPI REST API ↔ SQLite / PostgreSQL
                                    ▼
                    React + TypeScript EHS Dashboard
```

---

## Core Features

- **Dual-Channel Intelligence**: Evaluates incident narratives through both statistical ML and deterministic physics rules (Gravity, Pressure, Electrical, Chemical, Mechanical Motion).
- **Categorical Reconciliation**: Reconciles independent channels into clear triage outcomes (`CONSENSUS_SIF`, `CONSENSUS_NON_SIF`, or `HUMAN REVIEW REQUIRED`). Discrepancies are never averaged away—they trigger mandatory human review.
- **Transparent Lexical Explainability**: Computes real-time token-level log-odds contributions ($w_j \cdot x_j$) for every active n-gram in the input text, providing full interpretability.
- **Strict Metadata Quarantine**: Ensures narrative-only inference. Outcome fields (hospitalizations, amputations, fatalities) are strictly barred from inference to prevent retrospective leakage.
- **Multi-Tenant Authentication**: Built-in bcrypt password hashing and JWT bearer authentication. Reports and analytics are partitioned per user account.
- **Safety Analytics Dashboard**: Visualizes incident distributions, reconciliation statuses, and controlling hazard energies with real-time KPI aggregations.

---

## Machine Learning Specifications

The production ML pipeline uses a frozen, calibrated statistical model trained on normalized incident narratives:

- **Model Family**: TF-IDF Vectorizer (4,886 word & bigram n-grams) + Logistic Regression
- **Regularization**: $C = 100.0$, `class_weight = "balanced"`
- **Calibrated Decision Threshold**: $\tau = 0.59$ (optimizes sensitivity to high-consequence events)
- **Evaluation Performance**:
  - **Precision**: 85.1%
  - **Recall**: 86.9%
  - **F1-Score**: 86.0%
  - **ROC-AUC**: 0.941
- **Score Semantics**: The model output is strictly the **"Model-estimated SIF precursor propensity"** ($[0.0, 1.0]$) reflecting alignment with high-energy hazard indicators under the V2.3 specification. It is never presented as a probability of death or injury.

---

## Automated Test Suite (384 Tests)

SIF Sentinel is verified by an automated test suite spanning core AI algorithms, REST APIs, database isolation, and frontend components:

### Run Python Backend & Core Intelligence Tests (358 Tests):
```bash
pytest -v
```

### Run React Frontend Component Tests (26 Tests):
```bash
cd frontend
npm test
```

### Run Frontend Production Build:
```bash
cd frontend
npm run build
```

**Test Baseline**: **384 / 384 tests passing**, zero errors, zero warnings.

---

## Manual Startup (Alternative)

If you prefer to run services in separate terminal windows:

### Terminal 1 (FastAPI Backend):
```bash
python -m uvicorn backend.app.main:app --port 8000
```

### Terminal 2 (React Frontend):
```bash
cd frontend
npm run dev
```

---

## Governance & Scientific Limitations

> [!IMPORTANT]
> **Decision Support Boundary**  
> SIF Sentinel is an engineering triage and decision-support tool designed to assist qualified Environmental Health & Safety (EHS) professionals. It does not make autonomous safety decisions, does not provide clinical or legal assessments, and does not replace qualified human safety investigation. All ambiguous or conflicting assessments require qualified human verification.
