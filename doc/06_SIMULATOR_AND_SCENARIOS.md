# Simulator & Scenario Catalog

This document details the telemetry generation physics engine, event injection mechanics, deterministic replay contract, and the full catalog of 12 pre-built test scenarios in TrackShift 2026.

---

## ⚙️ 1. Physics Telemetry Generator

The [`PhysicsTelemetryGenerator`](file:///e:/f1/simulator/generator/) produces 10Hz synthetic telemetry frames adhering to physical race dynamics:

- **Kinematics & Speed Curve**: Accelerates based on engine torque curves, limits top speed by aerodynamic drag ($F_{\text{drag}} \propto v^2$), and simulates realistic heavy braking into corners.
- **Tyre Wear Dynamics**: Wear accumulates proportionally to lateral/longitudinal G-forces, slip angle, and track surface roughness.
- **Thermal Mechanics**: Tyre temperatures heat up during cornering/braking ($+2.5^\circ\text{C/sec}$) and cool down on straights ($-1.2^\circ\text{C/sec}$).
- **Fuel Consumption**: Decreases fuel mass by ~1.6 kg per lap, increasing car acceleration as total weight reduces.

---

## 🎬 2. Dynamic Mid-Race Event Injectors

The simulator supports real-time event injection via dynamic event controllers ([`simulator/events/`](file:///e:/f1/simulator/events/)):

### Flag Period Injector (`FlagPeriod`)
Injects `SAFETY_CAR` or `VSC` flag conditions during specified lap intervals:
- Forces all cars to reduce speed to target delta delta times.
- Reduces pit loss penalty from 22.0s to 14.0s (VSC) or 11.0s (SC).

### Weather Transition Injector (`WeatherTransition`)
Simulates incoming weather fronts:
- Increases rain intensity from 0.0 to 1.0.
- Drops track surface temperatures.
- Degrades dry tyre pace by up to +15.0s/lap if dry tyres remain fitted during rain.

### Pit Stop Mechanics (`PitStopEvent`)
Simulates in-run pit stops:
- Caps speed at 80 km/h in pit lane.
- Simulates stationary box time (2.5s base + wheel nut variance).
- Resets tyre compound and tyre age to 0 laps.

---

## 📜 3. Catalog of 12 Seeded Test Scenarios

The [`ScenarioSuite`](file:///e:/f1/simulator/scenarios/suite.py) contains 12 deterministic, seeded scenarios designed to test every facet of the strategy engine.

| # | Scenario Name | Description | Key Objective / Trigger |
|---|---|---|---|
| 1 | `normal_race` | Standard 30-lap dry race with linear degradation. | Evaluates baseline 1-stop strategy (`MEDIUM` → `HARD`). |
| 2 | `tyre_cliff` | Accelerated tyre wear causing severe cliff at Lap 18. | Validates early detection of `TYRE_CLIFF_IMMINENT`. |
| 3 | `vsc_pit_opportunity` | VSC deployed on Lap 15 during pit window. | Tests opportunistic pit decision taking advantage of reduced pit loss (14.0s). |
| 4 | `sc_pit_opportunity` | Full Safety Car deployed on Lap 20. | Verifies double-stack or immediate pit stop call under full SC. |
| 5 | `opponent_undercut` | Rival car (CAR_02) pits 2 laps early for fresh Softs. | Tests `OPPONENT_UNDERCUT_THREAT` event & counter-strategy (`PIT_NOW`). |
| 6 | `opponent_overcut` | Rival stays out on clear track while ego car encounters traffic. | Evaluates overcut protection and gap calculations. |
| 7 | `rain_arrival` | Rain begins at Lap 22 (rain intensity 0.85). | Validates timely transition from dry slicks to `INTERMEDIATE` tyres. |
| 8 | `heavy_traffic` | Re-entering track into a cluster of 4 backmarkers. | Tests traffic risk weight penalty in objective function. |
| 9 | `telemetry_corruption` | Sensor spikes and negative speeds injected at Lap 10. | Verifies outlier filtering and range clamping in `NormalizationPipeline`. |
| 10 | `missing_telemetry` | Complete 5-second telemetry blackout at Lap 14. | Tests Last-Observation-Carried-Forward (LOCF) state retention. |
| 11 | `strategy_inferiority` | Fixed naive baseline strategy vs. AI strategy engine. | Measures net race time saved by AI strategy optimizer. |
| 12 | `driver_disagreement` | Driver reports destroyed tyres while telemetry indicates 82% grip. | Tests `HUMAN_AI_DISAGREEMENT` detection & alert engine. |

---

## 🛠️ 4. Programmatic Scenario Definition

You can create new scenarios programmatically using `ScenarioDefinition`:

```python
from simulator.scenarios.model import ScenarioDefinition
from simulator.events import FlagPeriod, WeatherTransition

custom_scenario = ScenarioDefinition(
    scenario_id="monaco_vsc_rain",
    description="Monaco wet race with late VSC",
    total_laps=40,
    seed=42,
    flag_periods=[
        FlagPeriod(start_lap=25, end_lap=28, flag_type="VSC")
    ],
    weather_transitions=[
        WeatherTransition(start_lap=20, target_intensity=0.90)
    ]
)
```
