# Radio Intelligence & Human-AI Disagreement Engine

This document details the audio transcription pipeline, driver intent NLP extraction, and the Human-AI Disagreement Detection engine in TrackShift 2026.

---

## 🎙️ 1. Asynchronous Audio Pipeline Architecture

In Formula 1 pit wall operations, team radio communications are a vital source of driver feedback. However, driver complaints can be subjective, emotional, or misleading. 

TrackShift processes audio feeds asynchronously using [`RadioTranscriptionService`](file:///e:/f1/radio/transcription/) so that audio ingestion **never blocks the 10Hz strategy decision loop**.

```
[ Driver Radio Audio ] ──> (Async Thread Queue) ──> [ Transcription Service ]
                                                            │ Raw Text
                                                            ▼
                                                [ NLP Intent Extractor ]
                                                            │ Semantic Intent
                                                            ▼
                                                [ Disagreement Detector ]
                                                            │ Cross-Reference
                                                            ▼
                                                [ Pit Wall Alert Widget ]
```

---

## 🧠 2. NLP Semantic Intent Extraction

The [`RadioIntentExtractor`](file:///e:/f1/radio/extraction/) maps transcribed audio into structured intent records (`DriverRadioMessage`):

| Keyword Pattern / Phrase | Extracted Intent | Semantic Payload |
|---|---|---|
| *"Tyres are gone"* / *"No rear grip"* | `TYRE_WEAR_HIGH` | `severity: HIGH` |
| *"Hitting the wall"* / *"Pace dropping fast"* | `CLIFF_IMMINENT` | `severity: CRITICAL` |
| *"Box this lap"* / *"In in in"* | `PIT_REQUEST` | `requested_compound: OPTIONAL` |
| *"Rain at turn 3"* / *"Spotting drops"* | `RAIN_REPORT` | `location: TURN_3` |
| *"He's backing me up"* / *"Stuck behind"* | `TRAFFIC_COMPLAINT` | `target_car: AHEAD` |

---

## ⚡ 3. The 5 Human-AI Conflict Detection Rules

The [`HumanAIDisagreementDetector`](file:///e:/f1/radio/disagreement.py) cross-references driver radio claims against objective telemetry metrics across 5 conflict categories:

### Rule 1: `TYRE_WEAR_CONFLICT`
- **Trigger**: Driver reports severe wear (*"Tyres are dead"*), but telemetry model indicates wear fraction $< 35\%$.
- **Interpretation**: Driver is managing pace or over-reacting to a single slide.
- **Recommended Action**: Inform driver that telemetry shows healthy tread; maintain strategy.

### Rule 2: `CLIFF_IMMINENCE_CONFLICT`
- **Trigger**: Driver reports tyres feel fine, but Bayesian posterior indicates cliff onset within $< 2$ laps.
- **Interpretation**: Thermal degradation is hidden until sudden grip loss occurs.
- **Recommended Action**: Warn pit wall to prepare for immediate pit stop next lap.

### Rule 3: `STRATEGY_CALL_CONFLICT`
- **Trigger**: Driver requests immediate pit stop, but Strategy Engine determines `STAY_OUT` yields $-8.5\text{s}$ faster race time.
- **Interpretation**: Driver is anxious about position loss without field gap visibility.
- **Recommended Action**: Provide expected time loss breakdown to race engineer.

### Rule 4: `WEATHER_CONFLICT`
- **Trigger**: Driver reports rain on track, but weather trend regression indicates zero moisture (<0.05 intensity).
- **Interpretation**: Isolated moisture or false alarm; changing to intermediates will lose 25+ seconds.
- **Recommended Action**: Hold pit stop until radar confirms widespread rain.

### Rule 5: `TRAFFIC_GAP_CONFLICT`
- **Trigger**: Driver complains of severe traffic dirty air, but interval to car ahead is $> 3.2$ seconds (beyond turbulent wake zone).
- **Interpretation**: Driver pace drop is self-induced, not caused by dirty air.
- **Recommended Action**: Focus driver on corner entry braking points.

---

## 📺 4. Pitwall Alert Integration

When a high-severity disagreement is detected, the engine broadcasts a `HUMAN_AI_DISAGREEMENT` WebSocket event to the frontend:

```json
{
  "event_type": "HUMAN_AI_DISAGREEMENT",
  "car_id": "VER",
  "disagreement_type": "TYRE_WEAR_CONFLICT",
  "driver_claim": "Tyres are completely gone, request box",
  "ai_telemetry_finding": "Telemetry indicates 78% grip remaining; WLS pace loss only +0.12s/lap",
  "severity": "HIGH",
  "recommended_action": "STAY_OUT for 4 more laps to clear traffic window"
}
```
