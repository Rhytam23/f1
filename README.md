# TrackShift 2026 — Race Intelligence Engine & DegradIQ

> We don't predict tyres. We predict decisions.

An end-to-end, simulator-independent race intelligence platform built for **TrackShift 2026**.

The repository integrates two core layers:
1. **DegradIQ (`degradiq/`)**: The dedicated **Tyre Degradation Isolation Subsystem** solving the core TrackShift 2026 challenge. Isolates true physical tyre wear from noisy practice telemetry (de-fueling, de-trafficking, track evolution cleaning), fits a piecewise-linear Hinge degradation model, validates against race pace with low MAE (e.g., 0.38s at Monza Hard), and visualizes results via an interactive Streamlit dashboard.
2. **Race Intelligence Engine (`backend/`, `frontend/`, `simulator/`, `radio/`, `evaluation/`)**: Real-time pit wall decision engine turning telemetry into explainable strategic recommendations (`PIT`, `STAY_OUT`, `UNDERCUT`, `OVERCUT`, `DEFEND`, `ATTACK`) with confidence ratings, driver radio conflict detection, Monte Carlo position prediction, and interactive web dashboards.

Full documentation index and architecture guides: [doc/INDEX.md](doc/INDEX.md).

---

## Repository Layout

```
degradiq/    Tyre Degradation Isolation Subsystem (Streamlit dashboard, hinge models, validation)
frontend/    Pit Wall & Strategic HQ dashboards, 14-corner SVG track viz, telemetry inspector
backend/     Ingestion → 10-stage normalization → state estimation → pace/tyre/opponent estimators →
             event detection → strategy decision engine → Monte Carlo prediction → WebSocket
simulator/   Telemetry generator, seeded scenario engine (12 scenarios), pit stop simulation, replay
radio/       Async audio transcription & human/AI conflict detection (5 disagreement rules)
evaluation/  Backtesting engine, latency benchmarking (<2s targets), stress testing
data/        Cached FastF1 telemetry & race session pickles
doc/         Comprehensive 10-part technical documentation suite
tests/       Unit, interface, scenario, and integration test suite (256/256 passing)
```

---

## Quick Start

### 1. DegradIQ Streamlit Dashboard (Tyre Wear Isolation)
To view the interactive tyre degradation curves, noise attribution (fuel vs. track vs. wear), validation MAE, and pit-window recommendations:

```bash
# Using the DegradIQ environment:
degradiq\.venv\Scripts\python.exe -m streamlit run degradiq/dashboard.py
```

### 2. Race Intelligence Engine (Live Pit Wall Demo)
To launch the end-to-end race decision engine with live scenario playback, embedded REST API, and web pit wall dashboard:

```bash
# Using the main environment:
.venv\Scripts\activate
python demo.py --scenario tyre_cliff --speed 2.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser to view the live Pit Wall & HQ dashboard.

### 3. Running Tests
```bash
.venv\Scripts\activate
pytest
```
*All 256 unit, scenario, and integration tests passing.*

---

## Engineering Principles

- **Physics-Informed Models First**: Physical degradation models (piecewise-linear hinge wear curve, fuel burn weight correction) take precedence; ML models validate and refine.
- **Explainable Strategy**: The strategy engine decides (`PIT` / `STAY_OUT` / `UNDERCUT`); driver radio intelligence detects human-AI divergence; every recommendation carries an audit reason and confidence score.
- **Zero Hallucinated Numbers**: Every confidence, degradation slope, and delta traces back to real FastF1 session telemetry or physics-calibrated simulation.
- **Strict Subsystem Isolation**: DegradIQ operates as a self-contained analysis module while seamlessly providing calibrated tyre degradation parameters to the broader pit wall decision pipeline.

---

## 📖 Project Understanding (Future Reference)

Built for the TrackShift 2026 competition. Two integrated layers: DegradIQ isolates true tyre
wear from noisy practice telemetry (de-fueling, de-trafficking, track evolution) using a
piecewise-linear "Hinge" degradation model validated against real race pace (e.g. 0.38s MAE at
Monza); the Race Intelligence Engine turns live telemetry into explainable pit-wall
recommendations (PIT/STAY_OUT/UNDERCUT/OVERCUT/DEFEND/ATTACK) with Monte Carlo position
prediction and driver-radio conflict detection. 256/256 tests passing per its own docs.

**Stack:** Python (FastAPI, pandas, scikit-learn, xgboost) backend + Streamlit dashboard +
frontend dashboards; simulator and backtesting/evaluation harness included.
**Status:** competition submission for TrackShift 2026 — the most technically deep repo in your
account, with a real test suite and documentation index (`doc/INDEX.md`).

## 🎯 Where This Can Be Used

- Motorsport/sports-analytics portfolio piece — the tyre-degradation isolation work in
  particular is genuinely novel methodology, worth highlighting on its own.
- Reference architecture for any "noisy real-time telemetry → explainable decision engine"
  problem outside racing (e.g. any domain with sensor noise + high-stakes real-time calls).
- **Hackathons:** built for one, and reusable for the next — the backtesting/evaluation harness
  and simulator are a strong base for any future real-time-decision-engine hackathon track.
