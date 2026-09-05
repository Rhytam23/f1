# System Architecture & Data Pipeline Flow

This document details the high-level architecture, module interactions, and end-to-end real-time data processing pipeline of the **TrackShift 2026 Race Intelligence Engine**.

---

## 🏗️ High-Level System Architecture

TrackShift is structured as a decoupled, multi-stage processing pipeline where raw telemetry frames are incrementally transformed into normalized state estimates, intelligence signals, discrete event alerts, and optimal strategy decisions.

```
                    ┌───────────────────────────────┐
                    │    Telemetry Source Adapter   │
                    │ (Simulator / Replay / Live)   │
                    └───────────────┬───────────────┘
                                    │ Raw Telemetry Frame
                                    ▼
                    ┌───────────────────────────────┐
                    │     Normalization Stage       │
                    │ (Validation, Clamping, LOCF)  │
                    └───────────────┬───────────────┘
                                    │ NormalizationResult
                                    ▼
                    ┌───────────────────────────────┐
                    │     Race State Estimator      │
                    │ (Incremental Track & Car Map) │
                    └──────┬────────┬────────┬──────┘
                           │        │        │
         ┌─────────────────┘        │        └─────────────────┐
         ▼                          ▼                          ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│ Tyre Degradation │      │ Pace & Compounds │      │ Opponent Order & │
│   Intelligence   │      │   Intelligence   │      │ Undercut Predict │
└────────┬─────────┘      └────────┬─────────┘      └────────┬─────────┘
         │                         │                         │
         └─────────────────┬───────┴─────────────────────────┘
                           │
                           ▼
                    ┌───────────────────────────────┐
                    │     Event Detection Engine    │
                    │ (SC/VSC, Rain, Cliff, Loss)   │
                    └───────────────┬───────────────┘
                                    │ Event Stream
                                    ▼
                    ┌───────────────────────────────┐
                    │  Strategy Engine & Objective  │
                    │ (Multi-objective Pit Decision)│
                    └───────────────┬───────────────┘
                                    │ StrategyDecision + Rationale
                                    ▼
                    ┌───────────────────────────────┐
                    │ Monte Carlo Position Predictor│
                    │ (Trajectory & Outcome Bounds) │
                    └───────────────┬───────────────┘
                                    │
           ┌────────────────────────┴────────────────────────┐
           ▼                                                 ▼
┌──────────────────────────────┐          ┌──────────────────────────────┐
│ Decision Audit Logging (JSON)│          │ WebSocket & REST API Server  │
└──────────────────────────────┘          └───────────────┬──────────────┘
                                                          │ Real-time Stream
                                                          ▼
                                          ┌──────────────────────────────┐
                                          │ Pitwall & HQ Dashboards (UI) │
                                          └──────────────────────────────┘
```

---

## ───────── 1. Telemetry Ingestion & Normalization ─────────

### Source Adapters
The ingestion layer connects to telemetry producers via the [`SourceAdapter`](file:///e:/f1/backend/adapters/) interface. Three primary implementations exist:
1. [`SimulatorAdapter`](file:///e:/f1/backend/adapters/): Generates real-time synthetic physics telemetry.
2. [`ReplayAdapter`](file:///e:/f1/backend/adapters/): Replays pre-recorded telemetry files deterministically.
3. [`RealCarAdapter`](file:///e:/f1/backend/adapters/): Placeholder interface for live F1/FIA UDP telemetry streams.

### Normalization Pipeline
The [`NormalizationStage`](file:///e:/f1/backend/normalization/) applies 10 concrete validation and cleaning routines:
- **Timestamp Ordering**: Out-of-order packet resequencing.
- **Sensor Range Clamping**: Enforces physical boundaries (e.g. throttle `[0.0, 1.0]`, tyre temp `[50°C, 140°C]`).
- **Outlier Filtering**: Spikes exceeding 4-sigma moving bounds are filtered.
- **Last-Observation-Carried-Forward (LOCF)**: Prevents state corruption during temporary packet dropouts.
- **Provenance Envelope**: Wraps telemetry in a [`NormalizationResult`](file:///e:/f1/backend/normalization/) containing raw frame, cleaned frame, list of modifications, and quality confidence score.

---

## ───────── 2. Race State Estimation ─────────

The [`RaceStateEstimator`](file:///e:/f1/backend/state/) maintains the single source of truth for all cars on track:
- **Per-Car Telemetry History**: Rolling buffer of lap times, sector times, tyre compound, tyre age, speed, braking points, and gap differentials.
- **Track Status**: Current flag status (`GREEN`, `YELLOW`, `VSC`, `SAFETY_CAR`, `RED`), track surface state, and ambient/track temperature trends.
- **Order Tracker**: Position order, interval to car ahead, gap to leader, and pit window overlap metrics.

---

## ───────── 3. Intelligence Layers ─────────

### A. Tyre Degradation Intelligence ([`backend/tyre/`](file:///e:/f1/backend/tyre/))
- **Physics Decomposition**: Separates base driver pace, fuel mass correction (~0.03s per lap per kg fuel burned), and track evolution from true thermal/mechanical degradation.
- **Weighted Least Squares (WLS) & Bayesian Fit**: Fits compound wear curves and computes Bayesian posterior probability of cliff onset lap.

### B. Pace Intelligence ([`backend/pace/`](file:///e:/f1/backend/pace/))
- Estimates instantaneous degradation-free pace per driver and projects lap times across soft, medium, and hard compounds over remaining stint lengths.

### C. Opponent Intelligence ([`backend/opponents/`](file:///e:/f1/backend/opponents/))
- Tracks multi-car field positions, computes undercut/overcut vulnerability metrics, and forecasts opponent pit windows.

### D. Racing Line Intelligence ([`backend/racing_line/`](file:///e:/f1/backend/racing_line/))
- Analyzes corner-by-corner telemetry (braking points, entry/apex/exit speed, trajectory deviation) to classify driving lines (`IDEAL`, `ATTACKING`, `DEFENSIVE`) and detect corner time loss.

### E. Radio Intelligence & Disagreement ([`radio/`](file:///e:/f1/radio/))
- Asynchronously transcribes team radio audio, extracts driver intent, and evaluates Human-AI disagreements (e.g., driver reporting heavy wear while telemetry shows nominal degradation).

---

## ───────── 4. Event Detection Engine ─────────

The [`EventDetector`](file:///e:/f1/backend/events/detector.py) continuously inspects state streams for 15 discrete event triggers:
- `SAFETY_CAR` / `VSC` flag transitions.
- `RAIN_INCOMING` / `TRACK_DRYING` weather events.
- `TYRE_CLIFF_IMMINENT` / `DEGRADATION_ACCELERATING`.
- `FREE_PIT_WINDOW_OPEN` / `TRAFFIC_BLOCKAGE`.
- `HUMAN_AI_DISAGREEMENT` alerts.

---

## ───────── 5. Strategy Engine & Objective Optimization ─────────

The [`StrategyEngine`](file:///e:/f1/backend/strategy/engine.py) formulates pit decisions as a multi-objective cost optimization problem:

$$\text{Cost}(\text{Action}) = \text{ProjectedRaceTime}(\text{Action}) + w_1 \cdot \text{TrafficRisk} + w_2 \cdot \text{WeatherRisk} + \text{Penalty}(\text{Invalidation})$$

- Evaluates actions: `STAY_OUT`, `PIT_NOW_SOFT`, `PIT_NOW_MEDIUM`, `PIT_NOW_HARD`, `UNDERCUT`, `OVERCUT`.
- Calculates pit loss under green flag (~22.0s) vs. VSC (~14.0s) vs. Safety Car (~11.0s).
- Returns a structured [`StrategyDecision`](file:///e:/f1/backend/strategy/engine.py) containing primary recommendation, confidence percentage, expected time delta, top 3 decision reasons, and invalidation trigger conditions.

---

## ───────── 6. Position Prediction & Audit Logging ─────────

- **Monte Carlo Position Predictor** ([`models/position_model/`](file:///e:/f1/models/position_model/)): Simulates 1,000 forward race trajectories to estimate finishing position probability distributions (P1..P20 bounds).
- **Decision Audit Logger** ([`backend/observability/logging.py`](file:///e:/f1/backend/observability/logging.py)): Records structured JSON logs of every strategy output, input snapshot, model version, and predicted vs. actual outcome for complete post-race auditability.

---

## ───────── 7. Communication & Dashboard Layer ─────────

- **FastAPI REST API** ([`backend/api/app.py`](file:///e:/f1/backend/api/app.py)): Exposes endpoints for session status, scenario selection, manual event injection, and health checks.
- **WebSocket Manager** ([`backend/websocket/manager.py`](file:///e:/f1/backend/websocket/manager.py)): Broadcasts 10Hz telemetry updates, event notifications, strategy decisions, and driver radio transcripts to frontend subscribers.
- **Frontend Dashboards** ([`frontend/`](file:///e:/f1/frontend/)): HTML5/JS Pitwall Dashboard, Strategic HQ, and interactive 14-corner SVG track visualizer.
