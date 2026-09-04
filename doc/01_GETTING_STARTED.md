# Developer Quick Start & Setup Guide

This guide gets you up and running with **TrackShift 2026** on your local machine. It covers environment creation, dependency installation, running tests, executing the fast-forward interactive demo, and launching the live pitwall web application.

---

## 📋 Prerequisites

- **Python**: Version 3.10 or higher.
- **Operating System**: Windows, Linux, or macOS.
- **Tools**: Git, PowerShell / Bash.

---

## 🚀 Environment Setup

### 1. Clone & Navigate to Repository

```bash
git clone https://github.com/Rhytam23/f1.git
cd f1
```

### 2. Create and Activate Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\activate
```

**On Linux / macOS (Bash):**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

TrackShift uses modular dependency groups defined in [`pyproject.toml`](file:///e:/f1/pyproject.toml) so you can install only what you need.

#### Basic Development Install (Lightweight)
Installs core engine schemas (`pydantic`) and test utilities (`pytest`):
```bash
pip install -e ".[dev]"
```

#### Full Production / Full Suite Install
Installs FastAPI server dependencies, machine learning libraries (`numpy`, `xgboost`), and real-time visualization packages:
```bash
pip install -e ".[dev,api,ml,realtime]"
```

---

## 🧪 Running Unit & Integration Tests

The test suite validates all 30 engineering phases across 252 tests.

```bash
pytest
```

To run tests with detailed verbosity:
```bash
pytest -v
```

To run a specific test subsystem (e.g. strategy engine or scenarios):
```bash
pytest tests/test_strategy.py
pytest tests/test_scenarios.py
```

---

## 🏎️ Running the Interactive Fast-Forward Demo

TrackShift includes a self-contained, interactive demo script ([`demo.py`](file:///e:/f1/demo.py)) that streams real-time telemetry from any of the 12 pre-built scenarios into the race intelligence engine.

```bash
python demo.py
```

### Command-Line Arguments

| Argument | Options | Description | Default |
|---|---|---|---|
| `--scenario` | `normal_race`, `tyre_cliff`, `vsc_pit_opportunity`, `sc_pit_opportunity`, `opponent_undercut`, `opponent_overcut`, `rain_arrival`, `heavy_traffic`, `telemetry_corruption`, `missing_telemetry`, `strategy_inferiority`, `driver_disagreement` | Selects which race scenario to simulate. | `normal_race` |
| `--laps` | `1` to `70` | Total laps to run. | `30` |
| `--speed` | `1.0`, `5.0`, `10.0`, `100.0` | Simulation speed multiplier. | `10.0` |

### Example Command

Simulate a rainy race with driver radio disagreement at 20x speed:
```bash
python demo.py --scenario driver_disagreement --laps 25 --speed 20.0
```

---

## 🌐 Launching the Web Dashboards (Pitwall & HQ)

TrackShift includes a lightweight web dashboard containing the **Pitwall Hero View**, **Strategic HQ**, and **14-Corner Interactive Track SVG**.

### 1. Launch the Backend REST & WebSocket Server

```bash
uvicorn backend.api.app:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Open the Frontend Dashboards

Open your browser and navigate to:
- **Pitwall Hero Dashboard**: [`http://localhost:8000/`](http://localhost:8000/) or open [`frontend/index.html`](file:///e:/f1/frontend/index.html)
- **Strategic HQ Dashboard**: [`http://localhost:8000/hq/`](http://localhost:8000/hq/) or open [`frontend/hq/index.html`](file:///e:/f1/frontend/hq/index.html)
- **Interactive Track Telemetry**: Included in the Pitwall UI view.

---

## 📁 Repository Directory Overview

```
e:\f1\
├── backend/          Core engine: ingestion, normalization, estimators, strategy, WebSocket
├── models/           Tyre degradation models, pace predictors, Monte Carlo position engine
├── simulator/        Physics telemetry generator, flag/weather injections, 12 race scenarios
├── radio/            Async transcript processing, NLP intent extractor, disagreement detector
├── evaluation/       Backtesting evaluation framework, metrics suite, latency benchmarking
├── frontend/         Pitwall hero dashboard, Strategic HQ, interactive 14-corner SVG track
├── tests/            252 unit, integration, and scenario verification tests
├── doc/              Full project documentation suite (You are here)
├── demo.py           Fast-forward interactive CLI demo runner
├── pyproject.toml    Project metadata & dependency definitions
└── requirements.txt  Root requirements file
```

---

## 🛠️ Common Troubleshooting

### Missing Module Errors (`ImportError` / `ModuleNotFoundError`)
Ensure you installed the package in editable mode within your virtual environment:
```bash
pip install -e ".[dev,api,ml,realtime]"
```

### WebSocket Disconnections in Browser
If the pitwall dashboard fails to receive live updates, ensure `uvicorn` is running on port `8000` and CORS is not blocked.

### High Test Execution Time
To run pytest in parallel across CPU cores:
```bash
pip install pytest-xdist
pytest -n auto
```
