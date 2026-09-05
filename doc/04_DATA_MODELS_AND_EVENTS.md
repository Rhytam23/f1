# Data Models & Event Taxonomy

This document defines the core Pydantic schemas, data contracts, state representations, event types, and audit logging formats used across TrackShift 2026.

---

## 🏎️ 1. Telemetry Schemas

### `RaceTelemetry` ([`backend/events/model.py`](file:///e:/f1/backend/events/model.py))
The standard immutable data object representing a single telemetry snapshot from one car.

```python
class RaceTelemetry(BaseModel):
    timestamp: float              # UNIX epoch timestamp in seconds
    car_id: str                   # Car identifier (e.g. "VER", "HAM", "CAR_01")
    lap: int                      # Current lap number
    lap_distance_m: float         # Distance traveled in current lap (meters)
    speed_kmh: float              # Instantaneous speed (km/h)
    throttle: float               # Throttle position [0.0, 1.0]
    brake: float                  # Brake position [0.0, 1.0]
    gear: int                     # Selected gear [1..8]
    engine_rpm: float             # Engine RPM
    tyre_compound: str            # "SOFT", "MEDIUM", "HARD", "INTERMEDIATE", "WET"
    tyre_age_laps: int            # Number of laps completed on current set
    tyre_wear_fl: float           # Front-Left tyre wear percentage [0.0=new, 1.0=worn]
    tyre_wear_fr: float           # Front-Right tyre wear percentage
    tyre_wear_rl: float           # Rear-Left tyre wear percentage
    tyre_wear_rr: float           # Rear-Right tyre wear percentage
    tyre_temp_fl: float           # Front-Left tyre temperature (°C)
    tyre_temp_fr: float           # Front-Right tyre temperature (°C)
    tyre_temp_rl: float           # Rear-Left tyre temperature (°C)
    tyre_temp_rr: float           # Rear-Right tyre temperature (°C)
    fuel_remaining_kg: float      # Fuel remaining in tank (kg)
    brake_temp_fl: float          # Front-Left brake disk temperature (°C)
    drs_active: bool              # DRS state (True if flap open)
```

---

## 🧼 2. Normalization Envelope

### `NormalizationResult` ([`backend/normalization/`](file:///e:/f1/backend/normalization/))
Wraps telemetry frames with audit provenance after cleaning.

```python
class FieldChange(BaseModel):
    field_name: str
    original_value: Any
    normalized_value: Any
    reason: str

class NormalizationResult(BaseModel):
    raw_frame: RaceTelemetry
    normalized_frame: RaceTelemetry
    field_changes: List[FieldChange]
    data_quality_score: float     # Quality confidence [0.0 = corrupt, 1.0 = pristine]
    is_valid: bool
```

---

## 📊 3. Engine State Models

### `RaceState` ([`backend/state/`](file:///e:/f1/backend/state/))
Maintained by the [`RaceStateEstimator`](file:///e:/f1/backend/state/) for the entire field.

```python
class CarState(BaseModel):
    car_id: str
    current_position: int
    current_lap: int
    latest_telemetry: RaceTelemetry
    last_lap_time_s: Optional[float]
    best_lap_time_s: Optional[float]
    pit_stops_count: int
    stint_history: List[StintRecord]
    gap_to_leader_s: float
    interval_to_ahead_s: float

class RaceState(BaseModel):
    session_time_s: float
    total_laps: int
    flag_status: str              # "GREEN", "YELLOW", "VSC", "SAFETY_CAR", "RED"
    track_temp_c: float
    ambient_temp_c: float
    rain_intensity: float         # [0.0 = dry, 1.0 = monsoon]
    car_states: Dict[str, CarState]
```

---

## 🧠 4. Intelligence Outputs

### `TyreDegradationState` ([`backend/tyre/model.py`](file:///e:/f1/backend/tyre/model.py))
```python
class TyreDegradationState(BaseModel):
    car_id: str
    compound: str
    tyre_age_laps: int
    wear_fraction: float          # Average wear across all 4 tyres [0.0..1.0]
    thermal_degradation_s: float   # Lap time loss due to overheating (seconds)
    mechanical_degradation_s: float# Lap time loss due to rubber depletion (seconds)
    total_degradation_s: float    # Combined lap time loss
    cliff_imminent: bool          # True if cliff is within 2 laps
    cliff_predicted_lap: Optional[int] # Estimated lap of steep pace drop
    confidence: float
```

---

## ⚡ 5. Real-Time Event Taxonomy

The [`EventDetector`](file:///e:/f1/backend/events/detector.py) emits discrete events conforming to the `Event` schema:

```python
class EventType(str, Enum):
    SAFETY_CAR = "SAFETY_CAR"
    VSC = "VSC"
    GREEN_FLAG = "GREEN_FLAG"
    TYRE_CLIFF_IMMINENT = "TYRE_CLIFF_IMMINENT"
    DEGRADATION_ACCELERATING = "DEGRADATION_ACCELERATING"
    PACE_DROP = "PACE_DROP"
    FREE_PIT_WINDOW_OPEN = "FREE_PIT_WINDOW_OPEN"
    TRAFFIC_BLOCKAGE = "TRAFFIC_BLOCKAGE"
    RAIN_INCOMING = "RAIN_INCOMING"
    TRACK_DRYING = "TRACK_DRYING"
    OPPONENT_UNDERCUT_THREAT = "OPPONENT_UNDERCUT_THREAT"
    OPPONENT_PIT_STOP = "OPPONENT_PIT_STOP"
    RACING_LINE_DEGRADATION = "RACING_LINE_DEGRADATION"
    HUMAN_AI_DISAGREEMENT = "HUMAN_AI_DISAGREEMENT"
    RADIO_INTENT_DETECTED = "RADIO_INTENT_DETECTED"

class Event(BaseModel):
    event_id: str
    event_type: EventType
    timestamp: float
    car_id: Optional[str]
    severity: str                 # "INFO", "WARNING", "CRITICAL"
    description: str
    payload: Dict[str, Any]
```

---

## 🎯 6. Strategy Decision Model

### `StrategyDecision` ([`backend/strategy/engine.py`](file:///e:/f1/backend/strategy/engine.py))
Output returned by the Strategy Engine for pit wall decision-making.

```python
class ActionType(str, Enum):
    STAY_OUT = "STAY_OUT"
    PIT_NOW = "PIT_NOW"
    PIT_NEXT_LAP = "PIT_NEXT_LAP"
    UNDERCUT = "UNDERCUT"
    OVERCUT = "OVERCUT"
    DEFEND = "DEFEND"
    ATTACK = "ATTACK"

class StrategyDecision(BaseModel):
    car_id: str
    recommended_action: ActionType
    target_compound: Optional[str]# "SOFT", "MEDIUM", "HARD", "INTERMEDIATE"
    target_pit_lap: int
    confidence: float             # Recommendation confidence [0.0..1.0]
    expected_race_time_delta_s: float # Time saved vs staying out (negative = faster)
    expected_finish_position: float # Expected position (e.g. 2.4)
    top_reasons: List[str]        # Human-readable justification bullet points
    invalidation_conditions: List[str] # Triggers that void this recommendation
    timestamp: float
```

---

## 🎙️ 7. Radio & Disagreement Models

### `DriverRadioMessage` ([`radio/model.py`](file:///e:/f1/radio/model.py))
```python
class DriverRadioMessage(BaseModel):
    message_id: str
    timestamp: float
    car_id: str
    driver_name: str
    raw_transcript: str
    extracted_intent: str         # e.g. "TYRE_WEAR_HIGH", "PIT_NOW_REQUEST"
    confidence: float
```

### `HumanAIDisagreement` ([`radio/disagreement.py`](file:///e:/f1/radio/disagreement.py))
```python
class DisagreementType(str, Enum):
    TYRE_WEAR_CONFLICT = "TYRE_WEAR_CONFLICT"
    CLIFF_IMMINENCE_CONFLICT = "CLIFF_IMMINENCE_CONFLICT"
    STRATEGY_CALL_CONFLICT = "STRATEGY_CALL_CONFLICT"
    WEATHER_CONFLICT = "WEATHER_CONFLICT"
    TRAFFIC_GAP_CONFLICT = "TRAFFIC_GAP_CONFLICT"

class HumanAIDisagreement(BaseModel):
    conflict_id: str
    car_id: str
    disagreement_type: DisagreementType
    driver_claim: str
    ai_telemetry_finding: str
    severity: str                 # "LOW", "MEDIUM", "HIGH"
    recommended_action: str
```

---

## 📝 8. Decision Audit Log Format

Structured JSON audit log recorded by [`DecisionAuditLogger`](file:///e:/f1/backend/observability/logging.py) for post-race analysis:

```json
{
  "timestamp": 1757030100.5,
  "car_id": "VER",
  "current_lap": 24,
  "action": "PIT_NOW",
  "target_compound": "HARD",
  "confidence": 0.92,
  "expected_time_delta_s": -14.2,
  "top_reasons": [
    "VSC active: pit loss reduced from 22.0s to 13.8s",
    "Medium tyres reached cliff threshold (wear = 78%)",
    "Clean re-entry window ahead of HAM (gap: +4.2s)"
  ],
  "invalidation_conditions": [
    "VSC ends before pit entry line",
    "Track surface drops below 25°C"
  ],
  "model_version": "v1.5.0-phase30",
  "inputs_hash": "a8f9c2d7e1"
}
```
