# Frontend Dashboards & Track Visualization

This document describes the web dashboards, user interface components, interactive 14-corner track SVG visualization, and REST/WebSocket communication protocols.

---

## 🎨 1. Dashboard UI Architecture

TrackShift includes two specialized web dashboards built with HTML5, CSS custom properties, and vanilla JavaScript (`app.js`):

1. **Pitwall Hero Dashboard** ([`frontend/index.html`](file:///e:/f1/frontend/index.html)): Real-time decision dashboard tailored for the Chief Race Engineer.
2. **Strategic HQ Dashboard** ([`frontend/hq/index.html`](file:///e:/f1/frontend/hq/index.html)): Overview dashboard for team strategists tracking the full 20-car field.

---

## 🏎️ 2. Pitwall Hero Dashboard Layout

The Pitwall view is optimized for rapid decision-making under high pressure.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        TrackShift 2026 — Pitwall                       │
├──────────────────────────────────────┬─────────────────────────────────┤
│                                      │   HUMAN vs AI DISAGREEMENT      │
│     HERO STRATEGY DECISION CARD      │   [ALERT: TYRE WEAR CONFLICT]   │
│                                      ├─────────────────────────────────┤
│  RECOMMENDATION: PIT NOW ➔ HARD      │   LIVE DRIVER RADIO TRANSCRIPT  │
│  CONFIDENCE: 92%   DELTA: -14.2s     │   VER: "Tyres are completely    │
│  EXPECTED FINISH: P1                │   gone, box this lap"           │
│                                      ├─────────────────────────────────┤
│  REASONS:                            │   14-CORNER TRACK SVG VIZ       │
│  - VSC active (Pit loss: 14.0s)      │   [Interactive Circuit Layout]  │
│  - Tyre wear at 78% cliff threshold  │   Hover: Turn 4Apex: 142 km/h   │
└──────────────────────────────────────┴─────────────────────────────────┘
```

### Key Components

- **Dominant Hero Decision Card**: Displays the current primary action (`PIT_NOW`, `STAY_OUT`, `UNDERCUT`), recommended compound (`SOFT`, `MEDIUM`, `HARD`), confidence score (%), expected race time saved, and top 3 justification points.
- **Human vs. AI Disagreement Alert**: Flashes high-contrast warning banner when driver radio claims conflict with telemetry models.
- **Team Radio Feed**: Displays live transcribed driver communications with intent badges.

---

## 🏛️ 3. Strategic HQ Dashboard Layout

The Strategic HQ view ([`frontend/hq/index.html`](file:///e:/f1/frontend/hq/index.html)) provides broad field visibility:

- **Multi-Car Leaderboard**: Real-time position order, interval to car ahead, gap to leader, current compound, tyre age, and pit stop count.
- **Tyre Degradation Matrix**: Side-by-side comparative wear curves for ego car vs. rival cars.
- **Rain Probability Radar**: 10-minute linear regression forecast of track surface moisture.

---

## 🏁 4. Interactive 14-Corner SVG Track Visualizer

The track visualizer ([`frontend/track/`](file:///e:/f1/frontend/track/)) renders an interactive 14-corner SVG circuit map:

- **Real-Time Car Position Marker**: Smoothly animates ego car position along the track trajectory based on `lap_distance_m`.
- **Corner Telemetry Inspector**: Hovering over any corner node (Turns 1 through 14) displays a telemetry popover inspect card:
  - Braking point & braking intensity ($g$-force).
  - Entry speed, Apex speed, and Exit speed.
  - Driving line classification (`IDEAL`, `ATTACKING`, `DEFENSIVE`).
  - Corner time loss vs. baseline (e.g. $+0.14\text{s}$).

---

## 🔌 5. API & WebSocket Protocol

### WebSocket Event Payload ([`backend/websocket/manager.py`](file:///e:/f1/backend/websocket/manager.py))

Clients connect via `ws://localhost:8000/ws/telemetry` to receive 10Hz updates:

```json
{
  "event_type": "TELEMETRY_UPDATE",
  "data": {
    "timestamp": 1757030100.5,
    "car_id": "VER",
    "lap": 24,
    "speed_kmh": 312.4,
    "tyre_compound": "MEDIUM",
    "tyre_wear_avg": 0.68,
    "strategy_decision": {
      "action": "PIT_NOW",
      "target_compound": "HARD",
      "confidence": 0.92,
      "expected_delta_s": -14.2
    }
  }
}
```

### REST API Endpoints ([`backend/api/app.py`](file:///e:/f1/backend/api/app.py))

| Endpoint | Method | Description |
|---|---|---|
| `/api/status` | `GET` | Returns current engine status, connected clients, and active scenario. |
| `/api/scenario` | `POST` | Switches active scenario (e.g. `{"scenario_id": "rain_arrival"}`). |
| `/api/inject_event` | `POST` | Manually injects Safety Car, VSC, or rain event. |
| `/health` | `GET` | System health check endpoint. |
