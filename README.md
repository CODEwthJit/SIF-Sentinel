# SIF Sentinel — AI-Powered Safety Intelligence

A local-first, full-stack safety intelligence platform for identifying **Serious Injury & Fatality (SIF) Precursors** from unstructured workplace incident narratives.

SIF Sentinel pairs a calibrated statistical machine learning model with a deterministic engineering rule engine in a dual-channel architecture. Disagreements between the two channels are systematically surfaced through an auditable categorical reconciliation engine to gate high-risk or ambiguous incidents for qualified human safety professional review.

*(Developed as a production-oriented, local-first full-stack portfolio application).*

---

## Why SIF Sentinel?

In industrial safety management, conventional incident reporting often focuses on the **actual outcome**—whether an event resulted in a minor first-aid case, a recordable injury, or no injury at all. However, modern safety science demonstrates that:

$$\text{Actual Outcome} \neq \text{SIF Potential}$$

A worker tripping over an uneven surface in a parking lot may break an arm (high actual outcome, low SIF potential), whereas a worker dropping a 20 lb wrench from a 30-foot scaffold without tethering may injure nobody solely due to lucky timing (zero actual outcome, extreme SIF potential).

SIF Sentinel asks a fundamentally different question: **Does the narrative describe conditions, energy sources, or barrier failures that possessed the propensity to cause a life-threatening or life-altering event?**

---

## How It Works

```text
Incident Narrative
        │
        ▼
Text Normalization & Tokenization
        │
        ├───────────────────────────────────────┐
        ▼                                       ▼
Statistical Machine Learning            Deterministic Rules
TF-IDF + Logistic Regression            V2.3 Safety-Rule Framework
(Propensity Score & Lexical Tokens)     (Hazard Energy & Rule Code)
        │                                       │
        └───────────────────┬───────────────────┘
                            ▼
               Reconciliation Engine
             (5-State Categorical Matrix)
                            │
                            ▼
                    Auditable Result
           [Consensus or Discrepancy]
                            │
                            ▼
              Human Review When Required
       (Mandatory Triage for Disagreements)
```

---

## Core Features

- **Dual-Channel Intelligence**: Concurrently evaluates incident narratives through both statistical machine learning and the project's deterministic V2.3 safety-rule framework.
- **Categorical Reconciliation**: Reconciles independent channels into clear categorical triage outcomes. Discrepancies and uncertainties are never averaged away—they are elevated for human safety expert review.
- **Transparent Lexical Explainability**: Computes real-time token-level log-odds contributions ($w_j \cdot x_j$) for all active n-grams in the narrative, enabling complete visibility into model decisions.
- **Strict Metadata Quarantine**: Strictly enforces narrative-only inference. Retrospective outcome fields (e.g., recorded days away, hospitalization, injury severity codes) are completely barred from the feature space to prevent retrospective leakage.
- **Multi-Tenant Authentication**: Built-in bcrypt password hashing and JWT bearer authentication. Reports, dashboard metrics, and audit records are partitioned per user account.
- **Interactive EHS Dashboard**: Provides real-time visibility into precursor propensity distributions, hazard energy mechanisms, triage priorities, and audit queues.
- **Human-in-the-Loop Review Pathway**: Gated workflows route conflicting or ambiguous incidents to safety engineers with full contextual rationale.

---

## System Architecture

```
                       Unstructured Safety Narrative
                                    │
                        ┌───────────┴───────────┐
                        ▼                       ▼
            ┌───────────────────────┐   ┌───────────────────────┐
            │   Machine Learning    │   │  Deterministic Rules  │
            │  TF-IDF + LogReg      │   │  V2.3 Safety Framework│
            │  (Threshold τ = 0.59) │   │  (Physical Energies)  │
            └───────────┬───────────┘   └───────────┬───────────┘
                        │                           │
                        │    ML Score & Tokens      │    Energy & Rule Code
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

## Machine Learning Specifications

The application utilizes a **final frozen machine learning model** evaluated strictly on normalized incident narratives:

- **Model Family**: TF-IDF Vectorizer (unigrams + bigrams) + Logistic Regression
- **Hyperparameters**: $C = 100.0$, `class_weight = "balanced"`
- **Vocabulary Size**: 4,886 features
- **Calibrated Decision Threshold**: $\tau = 0.59$ (calibrated via precision-recall curve analysis)
- **Score Semantics**: The model output is strictly the **"Model-estimated SIF precursor propensity"** ($[0.0, 1.0]$). It is **not** a probability of death, injury, or legal OSHA recordability.
- **Feature Attribution**: Real-time token importance computed via sparse TF-IDF weights multiplied by logistic regression coefficients.

### Final Frozen Model Evaluation

The frozen model was evaluated on the held-out test split against the project's provisional automated V2.3 labels:

| Metric | Score |
| :--- | :--- |
| **Accuracy** | **96.60%** |
| **Macro F1** | **0.9456** |
| **Macro Precision** | **0.9291** |
| **Macro Recall** | **0.9648** |
| **YES (SIF) Precision** | **0.9915** |
| **YES (SIF) Recall** | **0.9667** |
| **YES (SIF) F1-Score** | **0.9789** |
| **NO (Non-SIF) Precision** | **0.8667** |
| **NO (Non-SIF) Recall** | **0.9630** |
| **NO (Non-SIF) F1-Score** | **0.9123** |
| **ROC-AUC** | **0.9954** |
| **PR-AUC** | **0.9990** |

**Confusion Matrix:**
- **True Negatives (TN)**: 26
- **False Positives (FP)**: 1
- **False Negatives (FN)**: 4
- **True Positives (TP)**: 116

> [!NOTE]
> **Scientific Limitation & Label Provenance:**  
> These metrics measure agreement with the project's provisional automated annotation framework rather than independently human-validated SIF ground truth. Independent expert human validation would be required prior to any operational safety deployment.

---

## Categorical Reconciliation Matrix

Disagreements and confidence boundaries between the ML predictor and deterministic rules are resolved into five distinct states:

| Reconciliation Status | ML Channel ($\tau \ge 0.59$) | V2.3 Safety Rules | Review Required | Priority Tier |
| :--- | :---: | :---: | :---: | :---: |
| `CONSENSUS_SIF` | Positive | Positive | False | HIGH |
| `CONSENSUS_NON_SIF` | Negative | Negative | False | LOW |
| `RULE_UNCERTAIN_ML_SIGNAL` | Positive | Uncertain | **True** | HIGH |
| `RULE_UNCERTAIN_NO_ML_SIGNAL` | Negative | Uncertain | **True** | MEDIUM |
| `DIRECT_DISAGREEMENT` | Positive / Negative | Divergent | **True** | HIGH |

When the channels diverge or uncertainty is present, SIF Sentinel automatically flags the incident with `review_required = true` and assigns an operational triage priority for human verification.

---

## Quick Start (Single-Command Launch)

Run one command from the repository root to automatically verify prerequisites, audit dependencies, launch both backend and frontend servers, and open the application in your browser:

### Windows:
```cmd
run.bat
```
*(Or double-click `run.bat` in Windows Explorer)*

### macOS / Linux:
```bash
chmod +x run.sh
./run.sh
```

### Universal (Cross-Platform Python):
```bash
python run.py
```

### System Prerequisites:
- **Python**: 3.10 or higher
- **Node.js**: 18.0 or higher (with npm)

### What happens automatically:
1. **Prerequisite Check**: Verifies Python and Node.js versions.
2. **Port Conflict Protection**: Ensures ports `8000` (FastAPI) and `5173` (Vite) are available.
3. **Auto-Install Dependencies**: Installs missing Python packages from `requirements.txt` and frontend npm dependencies if needed.
4. **Dual Server Launch**: Boots the FastAPI backend and Vite React frontend concurrently.
5. **Readiness Verification**: Probes health endpoints until services are ready.
6. **Browser Auto-Launch**: Opens default browser directly to `http://localhost:5173/login`.
7. **Clean Shutdown**: Press **`Ctrl+C`** (Windows/Linux) or **`Cmd+C`** (macOS) to cleanly terminate all processes and free all ports.

---

## Application URLs

| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend Web App** | `http://localhost:5173` | React + TypeScript + Tailwind UI |
| **Login / Register** | `http://localhost:5173/login` | Authentication entrypoint |
| **Backend REST API** | `http://127.0.0.1:8000` | FastAPI service |
| **Interactive API Docs** | `http://127.0.0.1:8000/docs` | Swagger / OpenAPI Explorer |

---

## Automated Test Suite

The platform maintains comprehensive automated test coverage spanning machine learning components, rule engines, API endpoints, user isolation, and frontend React interfaces:

```bash
# Run Python backend & core intelligence tests:
pytest -v

# Run React frontend component tests:
cd frontend && npm test -- --run

# Run frontend production build:
cd frontend && npm run build
```

**Test Baseline**:
- **Python (`pytest`)**: 357 passed, 1 skipped (358 items collected)
- **Frontend (`vitest`)**: 26 passed (26 items collected)
- **Total Test Cases**: 384 automated test items across the full stack.

---

## Limitations & Safety Boundaries

> [!IMPORTANT]
> **Decision Support Boundary**  
> SIF Sentinel is an engineering triage and decision-support tool created as a portfolio application. It does **not** make autonomous safety decisions, does **not** provide medical or legal determinations, and does **not** replace certified Environmental Health & Safety (EHS) professionals.
>
> - **Not an Injury/Fatality Prediction**: The model calculates propensity of SIF precursor conditions described in text; it does not estimate the likelihood of worker death or injury.
> - **Provisional Automated Labels**: The underlying model was trained on labels generated by the project's deterministic V2.3 safety-rule framework, not on human-annotated ground truth.
> - **Mandatory Human Verification**: All ambiguous, conflicting, or high-priority flagged assessments require qualified human verification before taking any operational or remedial action.

---

## Project Status

- **Architecture**: Local-first full-stack portfolio application.
- **Deployment**: Intentionally designed and configured for local execution (no cloud deployment).
- **Intelligence**: Frozen machine learning weights, calibrated threshold ($\tau = 0.59$), and deterministic rules.
- **Repository**: Published on GitHub at [CODEwthJit/SIH26165](https://github.com/CODEwthJit/SIH26165).
