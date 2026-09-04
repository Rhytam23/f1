# Exhaustive Component Catalog

This document provides a complete inventory of every package, directory, module, primary class, and entry point in the TrackShift codebase.

---

## 📂 1. `backend/` — Race Intelligence Engine

The core backend package houses data ingestion, state estimation, strategy models, event detection, WebSocket communication, and REST endpoints.

| Directory / File | Key Classes / Functions | Primary Responsibility |
|---|---|---|
| [`backend/adapters/`](file:///e:/f1/backend/adapters/) | `SourceAdapter`, `SimulatorAdapter`, `ReplayAdapter`, `ReplayDescriptor` | Abstracts data sources; streams raw telemetry frames into the engine. |
| [`backend/ingestion/`](file:///e:/f1/backend/ingestion/) | `IngestionService`, `EventBus` | Decoupled publish-subscribe telemetry bus. |
| [`backend/normalization/`](file:///e:/f1/backend/normalization/) | `NormalizationPipeline`, `NormalizationStage`, `NormalizationResult`, `FieldChange` | Applies 10 cleaning/validation filters; attaches raw/cleaned provenance envelope. |
| [`backend/state/`](file:///e:/f1/backend/state/) | `RaceStateEstimator`, `RaceState`, `CarState` | Maintains real-time state of all cars, flag status, pit histories, and gap differentials. |
| [`backend/tyre/`](file:///e:/f1/backend/tyre/) | `TyreDegradationModel`, `TyreEstimator` | Fits WLS degradation curves; estimates thermal wear, mechanical wear, and cliff lap. |
| [`backend/pace/`](file:///e:/f1/backend/pace/) | `PaceEstimator`, `PaceModel` | Calculates degradation-free base pace and compound delta projections. |
| [`backend/opponents/`](file:///e:/f1/backend/opponents/) | `RaceOrderTracker`, `OpponentSummary`, `UndercutClassifier` | Tracks opponent pit windows, gap evolution, and undercut/overcut threats. |
| [`backend/racing_line/`](file:///e:/f1/backend/racing_line/) | `RacingLineEstimator`, `CornerTelemetry` | Corner-by-corner analysis (braking point, apex/exit speed, corner time loss). |
| [`backend/events/`](file:///e:/f1/backend/events/) | `EventDetector`, `Event`, `EventType` | Scans telemetry & state for 15 discrete real-time race events (SC, VSC, Rain, Cliff, etc.). |
| [`backend/strategy/`](file:///e:/f1/backend/strategy/) | `StrategyEngine`, `StrategyObjective`, `StrategyDecision` | Solves multi-objective pit action cost function (`STAY_OUT`, `PIT_SOFT`, `UNDERCUT`, etc.). |
| [`backend/weather/`](file:///e:/f1/backend/weather/) | `WeatherTrendDetector` | Linear regression on track temp & humidity to detect incoming rain. |
| [`backend/observability/`](file:///e:/f1/backend/observability/) | `DecisionAuditLogger`, `StructuredLogger` | Writes audit logs capturing decision rationale, inputs, model version, and predicted vs actual outcomes. |
| [`backend/api/`](file:///e:/f1/backend/api/) | `app.py`, FastAPI routes | REST endpoints (`/api/status`, `/api/scenario`, `/api/inject_event`, `/health`). |
| [`backend/websocket/`](file:///e:/f1/backend/websocket/) | `ConnectionManager` | Broadcasts 10Hz telemetry, strategy alerts, events, and radio transcripts. |

---

## 🤖 2. `models/` — Machine Learning Components

Houses statistical and physics-informed models for long-term forecasting.

| Directory / File | Key Classes / Functions | Primary Responsibility |
|---|---|---|
| [`models/tyre_model/`](file:///e:/f1/models/tyre_model/) | `TyreModelFitter` | Grid-searched degradation curve parameters and Bayesian posterior updating. |
| [`models/pace_model/`](file:///e:/f1/models/pace_model/) | `CompoundPacePredictor` | Compound-relative pace decomposition and fuel mass lap time correction. |
| [`models/position_model/`](file:///e:/f1/models/position_model/) | `MonteCarloPositionPredictor` | 1,000-run stochastic trajectory simulation for finishing position probability distribution. |
| [`models/uncertainty/`](file:///e:/f1/models/uncertainty/) | `UncertaintyEstimator` | Calculates confidence bounds and variance envelopes for strategy choices. |

---

## 🏎️ 3. `simulator/` — Telemetry & Scenario Engine

Generates synthetic telemetry, injects mid-race events, and runs repeatable scenario suites.

| Directory / File | Key Classes / Functions | Primary Responsibility |
|---|---|---|
| [`simulator/generator/`](file:///e:/f1/simulator/generator/) | `PhysicsTelemetryGenerator` | Simulates car kinematics, engine RPM, tyre temp, fuel consumption, and track position. |
| [`simulator/replay/`](file:///e:/f1/simulator/replay/) | `ReplayEngine` | Replays pre-recorded telemetry datasets with speed control and pause/resume. |
| [`simulator/events/`](file:///e:/f1/simulator/events/) | `FlagPeriod`, `WeatherTransition`, `PitStopEvent` | Dynamic event injectors for Safety Cars, rain start/stop, and in-run pit stop mechanics. |
| [`simulator/scenarios/`](file:///e:/f1/simulator/scenarios/) | `ScenarioSuite`, `ScenarioRunner`, `ScenarioDefinition` | Catalog of 12 seeded test scenarios (`normal_race`, `tyre_cliff`, `vsc_pit_opportunity`, etc.). |

---

## 📻 4. `radio/` — Team Radio & Disagreement Engine

Processes driver audio communications asynchronously without blocking the decision loop.

| Directory / File | Key Classes / Functions | Primary Responsibility |
|---|---|---|
| [`radio/transcription/`](file:///e:/f1/radio/transcription/) | `RadioTranscriptionService` | Non-blocking audio transcription service with deterministic fallback mode. |
| [`radio/extraction/`](file:///e:/f1/radio/extraction/) | `RadioIntentExtractor` | Semantic NLP keyword mapping (`DRIVER_TYRE_COMPLAINT`, `PIT_REQUEST`, `RAIN_REPORT`). |
| [`radio/disagreement.py`](file:///e:/f1/radio/disagreement.py) | `HumanAIDisagreementDetector` | Cross-references driver claims against telemetry metrics across 5 conflict types. |

---

## 📊 5. `evaluation/` — Backtesting & Benchmarks

Audits system performance, evaluates strategy efficacy, and enforces latency targets.

| Directory / File | Key Classes / Functions | Primary Responsibility |
|---|---|---|
| [`evaluation/backtesting/`](file:///e:/f1/evaluation/backtesting/) | `BacktestEngine`, `StrategyPerformanceMetrics` | Compares AI Strategy Engine against fixed/naive baseline strategies across all scenarios. |
| [`evaluation/metrics/`](file:///e:/f1/evaluation/metrics/) | `EvaluationReport`, `ScenarioEvaluationComparison` | Computes race time saved, position gain/loss, pit decision precision, and recall. |
| [`evaluation/latency/`](file:///e:/f1/evaluation/latency/) | `LatencyBenchmark` | Benchmarks pipeline processing stages under high frame rate (<2.0s mean target). |
| [`evaluation/stress_tests/`](file:///e:/f1/evaluation/stress_tests/) | `StressTestSuite` | Validates missing telemetry, packet corruption, high tick rate, and multi-car concurrency. |

---

## 💻 6. `frontend/` — Dashboards & Track Visualization

Lightweight HTML5/Vanilla CSS/JavaScript dashboards.

| Directory / File | Key Components | Description |
|---|---|---|
| [`frontend/index.html`](file:///e:/f1/frontend/index.html) | Pitwall Hero View | Primary race engineer view featuring hero decision card, telemetry, radio log, and disagreement alert. |
| [`frontend/hq/index.html`](file:///e:/f1/frontend/hq/index.html) | Strategic HQ Dashboard | Multi-car leaderboard, field position gap matrix, tyre degradation comparison, and rain radar. |
| [`frontend/track/`](file:///e:/f1/frontend/track/) | SVG Track Visualizer | Interactive 14-corner circuit diagram with telemetry hover inspector. |
| [`frontend/app.js`](file:///e:/f1/frontend/app.js) | Main JS Controller | Manages WebSocket connections, chart updates, and event notifications. |

---

## 🧪 7. `tests/` — Test Suite

Comprehensive test coverage passing 252/252 tests cleanly.

| Directory / File | Coverage Scope |
|---|---|
| [`tests/test_normalization.py`](file:///e:/f1/tests/test_normalization.py) | Normalization stages, clamping, outlier filtering, LOCF fallback. |
| [`tests/test_state.py`](file:///e:/f1/tests/test_state.py) | Race state estimator, order tracking, gap calculations. |
| [`tests/test_tyre.py`](file:///e:/f1/tests/test_tyre.py) | Tyre degradation fitting, cliff lap posterior detection. |
| [`tests/test_strategy.py`](file:///e:/f1/tests/test_strategy.py) | Strategy decision optimizer, compound selection, pit window valuation. |
| [`tests/test_events.py`](file:///e:/f1/tests/test_events.py) | Event detector triggers across 15 event types. |
| [`tests/test_scenarios.py`](file:///e:/f1/tests/test_scenarios.py) | End-to-end execution of all 12 seeded race scenarios. |
| [`tests/test_disagreement.py`](file:///e:/f1/tests/test_disagreement.py) | Human vs AI disagreement detection rules. |
| [`tests/test_latency.py`](file:///e:/f1/tests/test_latency.py) | Latency benchmark enforcement (<2.0s mean target). |
