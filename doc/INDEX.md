# TrackShift 2026 — Master Documentation Index

Welcome to the **TrackShift 2026 Race Intelligence Engine** documentation center. This directory (`doc/`) contains comprehensive technical documentation detailing every subsystem, algorithm, data structure, simulator scenario, radio processor, frontend dashboard, and testing framework within the repository.

---

## 📚 Complete Document Catalog

| File | Document Title | Description & Key Topics |
|---|---|---|
| [doc/INDEX.md](file:///e:/f1/doc/INDEX.md) | **Master Index & Onboarding Guide** | Overview of all documentation, directory map, and role-specific reading paths. |
| [doc/01_GETTING_STARTED.md](file:///e:/f1/doc/01_GETTING_STARTED.md) | **Developer Quick Start & Setup** | Installation, environment setup, dependency management, running unit tests (`pytest`), and launching the interactive demo (`demo.py`). |
| [doc/02_SYSTEM_ARCHITECTURE.md](file:///e:/f1/doc/02_SYSTEM_ARCHITECTURE.md) | **System Architecture & Pipeline Flow** | High-level data flow, module interaction, ingestion, state estimation, strategy engine, WebSocket broadcasting, and frontend integration. |
| [doc/03_COMPONENT_CATALOG.md](file:///e:/f1/doc/03_COMPONENT_CATALOG.md) | **Exhaustive Component Catalog** | Complete directory map of `backend/`, `models/`, `simulator/`, `radio/`, `evaluation/`, `frontend/`, and `tests/` with key classes and entry points. |
| [doc/04_DATA_MODELS_AND_EVENTS.md](file:///e:/f1/doc/04_DATA_MODELS_AND_EVENTS.md) | **Data Models & Event Taxonomy** | `RaceTelemetry` schemas, `RaceState`, `TyreDegradation`, `PaceModel`, `Event` types, `StrategyDecision`, `DriverRadioMessage`, and `DecisionAuditLog`. |
| [doc/05_STRATEGY_AND_MODELS.md](file:///e:/f1/doc/05_STRATEGY_AND_MODELS.md) | **Strategy Engine & Intelligence Models** | Physics-informed WLS tyre degradation fitting, Bayesian updates, pace projection, Monte Carlo position prediction, and multi-objective pit decision math. |
| [doc/06_SIMULATOR_AND_SCENARIOS.md](file:///e:/f1/doc/06_SIMULATOR_AND_SCENARIOS.md) | **Simulator & Scenario Catalog** | Telemetry generator physics, replay adapter, flag/weather injections, pit stop simulation, and the 12 pre-built test scenarios. |
| [doc/07_RADIO_AND_DISAGREEMENT.md](file:///e:/f1/doc/07_RADIO_AND_DISAGREEMENT.md) | **Radio Processing & Human-AI Conflicts** | Async audio transcription service, intent keyword extraction, and the 5 human/AI conflict detection rules (tyre, cliff, strategy, rain, traffic). |
| [doc/08_EVALUATION_AND_BENCHMARKS.md](file:///e:/f1/doc/08_EVALUATION_AND_BENCHMARKS.md) | **Evaluation, Backtesting & Latency** | `BacktestEngine`, baseline vs. AI strategy comparison, latency benchmarks (<2.0s targets), error handling, and security audit. |
| [doc/09_FRONTEND_DASHBOARDS.md](file:///e:/f1/doc/09_FRONTEND_DASHBOARDS.md) | **Frontend Pitwall & HQ Dashboards** | Pitwall dominant decision card, Strategic HQ leaderboard, interactive 14-corner SVG track visualization, telemetry inspector, and REST/WebSocket API endpoints. |
| [doc/10_PROJECT_STATUS_AND_ROADMAP.md](file:///e:/f1/doc/10_PROJECT_STATUS_AND_ROADMAP.md) | **Project Status & Future Roadmap** | Full audit of 30 completed phases (252/252 tests passing), system guarantees, engineering principles, and future real F1/FIA integration points. |

---

## 🎯 Role-Based Quick Paths

Depending on your role, we recommend reading the documentation in the following sequence:

### 🛠️ Backend / Infrastructure Engineers
1. [01_GETTING_STARTED.md](file:///e:/f1/doc/01_GETTING_STARTED.md) — Local environment & running `pytest`.
2. [02_SYSTEM_ARCHITECTURE.md](file:///e:/f1/doc/02_SYSTEM_ARCHITECTURE.md) — Data flow and ingestion mechanics.
3. [03_COMPONENT_CATALOG.md](file:///e:/f1/doc/03_COMPONENT_CATALOG.md) — `backend/` component breakdown.
4. [04_DATA_MODELS_AND_EVENTS.md](file:///e:/f1/doc/04_DATA_MODELS_AND_EVENTS.md) — Pydantic telemetry models and state schemas.

### 🧠 ML & Strategy Data Scientists
1. [02_SYSTEM_ARCHITECTURE.md](file:///e:/f1/doc/02_SYSTEM_ARCHITECTURE.md) — Pipeline placement of ML components.
2. [05_STRATEGY_AND_MODELS.md](file:///e:/f1/doc/05_STRATEGY_AND_MODELS.md) — Mathematical degradation models & Monte Carlo simulation.
3. [06_SIMULATOR_AND_SCENARIOS.md](file:///e:/f1/doc/06_SIMULATOR_AND_SCENARIOS.md) — Telemetry generator & scenario suites.
4. [08_EVALUATION_AND_BENCHMARKS.md](file:///e:/f1/doc/08_EVALUATION_AND_BENCHMARKS.md) — Backtesting engine & strategy metrics.

### 🎨 Frontend Developers
1. [01_GETTING_STARTED.md](file:///e:/f1/doc/01_GETTING_STARTED.md) — Launching web services and FastAPI endpoints.
2. [09_FRONTEND_DASHBOARDS.md](file:///e:/f1/doc/09_FRONTEND_DASHBOARDS.md) — Dashboard HTML/JS structure, track SVG, and WebSocket events.
3. [04_DATA_MODELS_AND_EVENTS.md](file:///e:/f1/doc/04_DATA_MODELS_AND_EVENTS.md) — JSON payloads delivered via WebSockets.

### 🧪 QA & Test Automation Engineers
1. [01_GETTING_STARTED.md](file:///e:/f1/doc/01_GETTING_STARTED.md) — Test setup and running `pytest`.
2. [06_SIMULATOR_AND_SCENARIOS.md](file:///e:/f1/doc/06_SIMULATOR_AND_SCENARIOS.md) — 12 seeded test scenarios.
3. [08_EVALUATION_AND_BENCHMARKS.md](file:///e:/f1/doc/08_EVALUATION_AND_BENCHMARKS.md) — Latency benchmarks, stress tests, and failure handling.
4. [10_PROJECT_STATUS_AND_ROADMAP.md](file:///e:/f1/doc/10_PROJECT_STATUS_AND_ROADMAP.md) — Verification records and phase breakdown.

---

## 🏛️ High-Level System Overview

```
[ Telemetry Source ] (Simulator / Replay / Live API)
         │
         ▼
[ Ingestion & Normalization ] ──> Clamping, Outlier Filter, Frame Validation
         │
         ▼
[ Race State Estimator ] ─────> Incremental Track & Car State
         │
         ├───> [ Tyre Degradation Intelligence ] (Physics-informed WLS + Bayesian)
         ├───> [ Pace Intelligence ]              (Compound Decomposition)
         ├───> [ Opponent Intelligence ]          (Undercut / Overcut / Order)
         └───> [ Racing Line Intelligence ]       (Corner Telemetry & Loss)
         │
         ▼
[ Event Detection Engine ] ───> SC / VSC / Rain / Cliff / Traffic / Disagreement
         │
         ▼
[ Strategy & Objective ] ─────> Multi-Objective Cost Minimization (Time + Risk)
         │
         ├───> [ Position Prediction ]            (Monte Carlo Trajectory Simulation)
         └───> [ Decision Audit Logging ]        (Structured Decision Rationale)
         │
         ▼
[ WebSocket & REST API ] ──────> Real-time Pitwall, HQ Dashboard, Track SVG
```

---

## 📍 Key Entry Points in Codebase

- **Fast-Forward Interactive Demo:** [`demo.py`](file:///e:/f1/demo.py)
- **FastAPI Web Server:** [`backend/api/app.py`](file:///e:/f1/backend/api/app.py)
- **Main Strategy Engine:** [`backend/strategy/engine.py`](file:///e:/f1/backend/strategy/engine.py)
- **Telemetry Physics Generator:** [`simulator/generator/physics.py`](file:///e:/f1/simulator/generator/physics.py)
- **Scenario Suite Catalog:** [`simulator/scenarios/suite.py`](file:///e:/f1/simulator/scenarios/suite.py)
- **Backtesting Evaluation:** [`evaluation/backtesting/engine.py`](file:///e:/f1/evaluation/backtesting/engine.py)
- **Pitwall Frontend HTML:** [`frontend/index.html`](file:///e:/f1/frontend/index.html)
