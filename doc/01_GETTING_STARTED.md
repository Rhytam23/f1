# Developer Quick Start & Setup Guide

This guide gets you up and running with **TrackShift 2026** and **DegradIQ** on your local machine. It covers environment creation, dependency installation, running tests, executing the interactive fast-forward race demo, and launching both the DegradIQ tyre degradation dashboard and the live pit wall web application.

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

## 🔬 Running the DegradIQ Streamlit Dashboard

**DegradIQ** is the dedicated tyre degradation isolation subsystem. It strips out fuel burn, track evolution, and traffic from practice telemetry, fits piecewise-linear hinge wear curves, and compares against actual race stint pace.

To launch the Streamlit dashboard:

```powershell
degradiq\.venv\Scripts\python.exe -m streamlit run degradiq/dashboard.py
```

Features:
- **Interactive Circuit / Compound Picker**: Monza (Hard), Bahrain (Soft), Spain (Medium).
- **Before/After Degradation Curves**: Live Plotly comparison of raw lap times vs. true wear slopes.
- **Noise Attribution Breakdown**: Fuel mass correction vs. true wear vs. track evolution.
- **Race Validation Panel**: Lap-by-lap comparison against real race stints with verified MAE (e.g. Monza Hard MAE: 0.38s).
- **Pit Window Recommendation**: Data-backed optimal pit stop window calculation.

---

## 🏎️ Running the Interactive Race Intelligence Demo

TrackShift includes an interactive demo script ([`demo.py`](file:///e:/f1/demo.py)) that streams real-time telemetry from any of the 12 pre-built scenarios into the race intelligence decision engine.

```bash
python demo.py --scenario tyre_cliff --speed 2.0
```

### Command-Line Arguments

| Argument | Options | Description | Default |
|---|---|---|---|
| `--scenario` | `normal_race`, `tyre_cliff`, `vsc_pit_opportunity`, `sc_pit_opportunity`, `opponent_undercut`, `opponent_overcut`, `rain_arrival`, `heavy_traffic`, `telemetry_corruption`, `missing_telemetry`, `strategy_inferiority`, `driver_disagreement` | Selects which race scenario to simulate. | `tyre_cliff` |
| `--speed` | `1.0`, `2.0`, `5.0`, `10.0` | Simulation speed multiplier. | `2.0` |
| `--port` | e.g. `8000` | Port for the live Pitwall API / WebSocket server. | `8000` |
| `--cli-only` | Flag | Run terminal decision log only without starting web server. | `False` |

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

## 🧪 Running Unit & Integration Tests

The test suite validates the entire architecture across 256 tests:

```bash
pytest
```

To run tests with detailed verbosity:
```bash
pytest -v
```

To run a specific test subsystem (e.g. strategy engine or scenarios):
```bash
pytest tests/test_strategy_engine.py
pytest tests/test_scenarios.py
```

---

## 📁 Repository Directory Overview

```
e:\f1\
├── degradiq/         Tyre degradation isolation pipeline, Streamlit dashboard, figures, and scripts
├── backend/          Core engine: ingestion, 10-stage normalization, estimators, strategy, WebSocket
├── simulator/        Physics telemetry generator, flag/weather injections, 12 race scenarios
├── radio/            Async transcript processing, NLP intent extractor, disagreement detector
├── evaluation/       Backtesting evaluation framework, metrics suite, latency benchmarking
├── frontend/         Pitwall hero dashboard, Strategic HQ, interactive 14-corner SVG track
├── data/             Cached FastF1 telemetry & race session pickles
├── tests/            256 unit, integration, and scenario verification tests (100% passing)
├── doc/              Full project documentation suite (You are here)
├── demo.py           Fast-forward interactive CLI & web demo runner
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

### Streamlit Dashboard Environment
If running the DegradIQ dashboard, ensure you execute it using the DegradIQ virtual environment:
```powershell
degradiq\.venv\Scripts\python.exe -m streamlit run degradiq/dashboard.py
```
