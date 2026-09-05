"""REST and WebSocket API server for TrackShift 2026 Race Intelligence Engine."""

from __future__ import annotations

import asyncio
from dataclasses import asdict
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from evaluation.backtesting.engine import BacktestEngine
from evaluation.latency.benchmark import LatencyBenchmark
from radio.transcription.service import RadioTranscriptionService
from simulator.scenarios.suite import NAMED_SCENARIOS, ScenarioRunner, create_scenario
from backend.websocket.manager import ConnectionManager

from backend.api.config import settings

app = FastAPI(
    title="RacePulse — Real-Time Telemetry & Strategy Engine",
    description="Simulator-independent, real-time F1 race intelligence and strategy REST/WebSocket API.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="dashboard")

manager = ConnectionManager()
radio_service = RadioTranscriptionService()
scenario_runner = ScenarioRunner()
backtest_engine = BacktestEngine(scenario_runner)
latency_benchmark = LatencyBenchmark()


class RadioIngestRequest(BaseModel):
    car_id: str = "44"
    lap: int = 1
    raw_text: str
    speaker: str = "DRIVER"


@app.get("/")
def read_root():
    return FileResponse("frontend/index.html")


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "engine": "RacePulse — Real-Time Telemetry & Strategy Engine",
        "version": "1.0.0",
        "scenarios_available": len(NAMED_SCENARIOS),
    }


@app.get("/api/circuits")
def list_circuits():
    from simulator.generator.track import silverstone_track, suzuka_track, default_track
    s_track = silverstone_track()
    z_track = suzuka_track()
    return [
        {
            "id": "silverstone",
            "name": s_track.name,
            "length_km": round(s_track.length_m / 1000.0, 3),
            "corner_count": len(s_track.corners),
            "corners": [
                {
                    "number": c.number,
                    "name": c.name,
                    "apex_distance_m": c.apex_distance_m,
                    "apex_speed_kph": c.apex_speed_kph,
                    "arc_length_m": c.arc_length_m,
                }
                for c in s_track.corners
            ],
        },
        {
            "id": "suzuka",
            "name": z_track.name,
            "length_km": round(z_track.length_m / 1000.0, 3),
            "corner_count": len(z_track.corners),
            "corners": [
                {
                    "number": c.number,
                    "name": c.name,
                    "apex_distance_m": c.apex_distance_m,
                    "apex_speed_kph": c.apex_speed_kph,
                    "arc_length_m": c.arc_length_m,
                }
                for c in z_track.corners
            ],
        },
    ]


@app.get("/api/scenarios")
def list_scenarios():
    catalog = []
    for sc_id in NAMED_SCENARIOS:
        sc = create_scenario(sc_id, seed=42)
        catalog.append({
            "scenario_id": sc.scenario_id,
            "name": sc.name,
            "description": sc.description,
            "seed": sc.seed,
            "primary_car_id": sc.primary_car_id,
            "num_cars": len(sc.generator_configs),
        })
    return catalog


@app.post("/api/scenarios/{scenario_id}/run")
def run_scenario(scenario_id: str, seed: int = 42):
    try:
        sc = create_scenario(scenario_id, seed=seed)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    states = scenario_runner.run(sc)

    serialized_states = {}
    for car_id, state in states.items():
        serialized_states[car_id] = {
            "car_id": state.car_id,
            "current_lap": state.current_lap,
            "position": state.position,
            "gap_ahead_s": state.gap_ahead_s,
            "gap_behind_s": state.gap_behind_s,
            "current_speed_kph": state.current_speed_kph,
            "tyre_compound": state.tyre_compound.value if state.tyre_compound else None,
            "tyre_age_laps": state.tyre_age_laps,
            "estimated_degradation_s": state.estimated_degradation_s,
            "degradation_rate_s_per_lap": state.degradation_rate_s_per_lap,
            "degradation_acceleration_s_per_lap2": state.degradation_acceleration_s_per_lap2,
            "tyre_cliff_probability": state.tyre_cliff_probability,
            "remaining_tyre_life_laps": state.remaining_tyre_life_laps,
            "current_pace_s": state.current_pace_s,
            "expected_clean_pace_s": state.expected_clean_pace_s,
            "pace_delta_s": state.pace_delta_s,
            "pace_trend_s_per_lap": state.pace_trend_s_per_lap,
            "fuel_load_kg": state.fuel_load_kg,
            "weather": state.weather.value if state.weather else "DRY",
            "rain_probability": state.rain_probability,
            "track_state": state.track_state.value if state.track_state else "GREEN",
            "safety_car": state.safety_car,
            "vsc": state.vsc,
            "current_strategy": state.current_strategy.to_dict() if state.current_strategy else None,
            "strategy_decision": state.current_strategy.decision.value if state.current_strategy else "STAY_OUT",
            "strategy_confidence": state.current_strategy.confidence if state.current_strategy else None,
            "reasons": state.current_strategy.reasons if state.current_strategy else [],
            "risks": state.current_strategy.risks if state.current_strategy else [],
            "invalidation_conditions": state.current_strategy.invalidation_conditions if state.current_strategy else [],
            "candidate_scores": state.current_strategy.candidate_scores if state.current_strategy else {},
            "opponent_threats": [
                {
                    "car_id": opp.car_id,
                    "position": opp.position,
                    "compound": opp.compound.value if opp.compound else None,
                    "tyre_age_laps": opp.tyre_age_laps,
                    "current_pace_s": opp.current_pace_s,
                    "degradation_rate_s_per_lap": opp.degradation_rate_s_per_lap,
                    "pit_probability": opp.pit_probability,
                    "gap_magnitude_s": opp.gap_magnitude_s,
                    "is_ahead": opp.is_ahead,
                    "undercut_threat": opp.undercut_threat.value if opp.undercut_threat else "NONE",
                    "overcut_threat": opp.overcut_threat.value if opp.overcut_threat else "NONE",
                }
                for opp in state.opponent_threats.values()
            ],
            "racing_line_analysis": {
                "total_time_loss_s": state.racing_line_analysis.total_time_loss_s,
                "overall_classification": state.racing_line_analysis.overall_classification.value,
                "line_degradation_detected": state.racing_line_analysis.line_degradation_detected,
                "corner_analyses": [
                    {
                        "corner_number": c.corner_number,
                        "corner_name": c.corner_name,
                        "braking_point_m": c.braking_point_m,
                        "braking_intensity": c.braking_intensity,
                        "entry_speed_kph": c.entry_speed_kph,
                        "apex_speed_kph": c.apex_speed_kph,
                        "exit_speed_kph": c.exit_speed_kph,
                        "line_deviation_m": c.line_deviation_m,
                        "time_loss_s": c.time_loss_s,
                        "classification": c.classification.value,
                    }
                    for c in (state.racing_line_analysis.corner_analyses if state.racing_line_analysis else [])
                ],
            } if state.racing_line_analysis else None,
            "disagreements": [
                {
                    "disagreement_type": d.disagreement_type.value,
                    "summary": d.summary,
                    "severity": d.severity,
                }
                for d in state.disagreements
            ],
            "latest_radio_message": {
                "speaker": state.latest_radio_message.speaker,
                "raw_text": state.latest_radio_message.raw_text,
                "lap": state.latest_radio_message.lap,
                "detected_intents": [i.value for i in state.latest_radio_message.detected_intents],
            } if state.latest_radio_message else None,
            "completed_laps": [
                {
                    "lap": l.lap,
                    "lap_time_s": l.lap_time_s,
                    "tyre_compound": l.tyre_compound.value if l.tyre_compound else None,
                    "tyre_age_laps": l.tyre_age_laps,
                    "was_pit_lap": l.was_pit_lap,
                }
                for l in state.completed_laps
            ],
        }

    return {
        "scenario_id": scenario_id,
        "seed": seed,
        "cars": serialized_states,
    }


@app.post("/api/radio")
async def ingest_radio(request: RadioIngestRequest):
    msg = await radio_service.transcribe_and_extract_async(
        car_id=request.car_id,
        lap=request.lap,
        raw_text=request.raw_text,
        speaker=request.speaker,
    )
    return {
        "message_id": msg.message_id,
        "car_id": msg.car_id,
        "lap": msg.lap,
        "speaker": msg.speaker,
        "raw_text": msg.raw_text,
        "detected_intents": [i.value for i in msg.detected_intents],
        "confidence": msg.confidence,
        "is_demo_mode": msg.is_demo_mode,
    }


@app.get("/api/telemetry/session/{circuit}")
def get_telemetry_session(circuit: str, driver: str = "VER", season: int = 2023):
    from data.loaders.fastf1_loader import load_fastf1_session_telemetry
    circuit_name = "Silverstone" if circuit.lower() == "silverstone" else "Suzuka"
    frames = load_fastf1_session_telemetry(season=season, circuit=circuit_name, session_type="R", driver=driver)
    if not frames:
        raise HTTPException(status_code=404, detail=f"No telemetry found for {circuit_name} {season} driver {driver}")
    
    laps = sorted(list(set(f.lap for f in frames)))
    compounds = list(set(f.tyre_compound.value for f in frames))
    return {
        "circuit": circuit_name,
        "season": season,
        "driver": driver,
        "data_classification": "REAL_TELEMETRY",
        "frame_count": len(frames),
        "laps": laps,
        "compounds": compounds,
        "sample_frames": [
            {
                "lap": f.lap,
                "speed_kph": f.speed_kph,
                "throttle_pct": f.throttle_pct,
                "brake_pct": f.brake_pct,
                "gear": f.gear,
                "rpm": f.rpm,
                "pos_x": f.pos_x,
                "pos_y": f.pos_y,
                "lap_distance_m": f.lap_distance_m,
                "tyre_compound": f.tyre_compound.value,
                "tyre_age_laps": f.tyre_age_laps,
            }
            for f in frames[::100]
        ],
    }


@app.get("/api/evaluation")
def get_evaluation_report(seed: int = 42):
    report = backtest_engine.run_full_evaluation(seed=seed)
    return asdict(report)


@app.get("/api/latency")
def get_latency_report(num_cars: int = 2, laps: int = 5):
    report = latency_benchmark.run_benchmark(num_cars=num_cars, laps=laps, tick_hz=5.0)
    return asdict(report)


@app.websocket("/ws/race")
async def race_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    replay_task: Optional[asyncio.Task] = None
    try:
        await websocket.send_json({"type": "CONNECTED", "engine": "RacePulse — Real-Time Telemetry & Strategy Engine"})
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_json({"type": "PONG"})
                continue

            try:
                import json
                payload = json.loads(data)
                action = payload.get("action")
                if action == "start_replay":
                    if replay_task and not replay_task.done():
                        replay_task.cancel()

                    circuit = payload.get("circuit", "silverstone")
                    driver = payload.get("driver", "VER")

                    async def _run_replay(circ: str, drv: str):
                        from backend.adapters.fastf1_adapter import FastF1Adapter
                        from backend.state.race_state import RaceState
                        from backend.tyre.estimator import TyreDegradationEstimator
                        from backend.strategy.engine import decide
                        from backend.state.baseline import LapRecord

                        circuit_name = "Silverstone" if circ.lower() == "silverstone" else "Suzuka"
                        adapter = FastF1Adapter(circuit=circuit_name, driver=drv, tick_delay_s=0.05)
                        await adapter.connect()

                        tyre_est = TyreDegradationEstimator()
                        state = RaceState(car_id=drv)

                        current_lap_num = -1
                        lap_start_fuel = 110.0

                        async for frame in adapter.stream():
                            state.current_lap = frame.lap
                            state.position = frame.position
                            state.current_speed_kph = frame.speed_kph
                            state.tyre_compound = frame.tyre_compound
                            state.tyre_age_laps = frame.tyre_age_laps
                            state.fuel_load_kg = frame.fuel_load_kg
                            state.track_state = frame.track_state
                            state.weather = frame.weather

                            if frame.lap != current_lap_num:
                                if current_lap_num > 0:
                                    rec = LapRecord(
                                        lap=current_lap_num,
                                        lap_time_s=88.5,
                                        tyre_compound=state.tyre_compound,
                                        tyre_age_laps=state.tyre_age_laps,
                                        fuel_load_kg_start=lap_start_fuel,
                                        avg_confidence=1.0,
                                    )
                                    state.completed_laps.append(rec)
                                current_lap_num = frame.lap
                                lap_start_fuel = frame.fuel_load_kg or 100.0

                            tyre_est.update(state)
                            decision = decide(state, tyre_est)
                            state.current_strategy = decision

                            msg = {
                                "type": "RACE_STATE_UPDATE",
                                "car_id": drv,
                                "circuit": circuit_name,
                                "data_classification": "HISTORICAL_REPLAY",
                                "current_lap": state.current_lap,
                                "position": state.position,
                                "speed_kph": frame.speed_kph,
                                "throttle_pct": frame.throttle_pct,
                                "brake_pct": frame.brake_pct,
                                "gear": frame.gear,
                                "rpm": frame.rpm,
                                "pos_x": frame.pos_x,
                                "pos_y": frame.pos_y,
                                "lap_distance_m": frame.lap_distance_m,
                                "tyre_compound": frame.tyre_compound.value if frame.tyre_compound else None,
                                "tyre_age_laps": frame.tyre_age_laps,
                                "estimated_degradation_s": state.estimated_degradation_s,
                                "degradation_rate_s_per_lap": state.degradation_rate_s_per_lap,
                                "degradation_acceleration_s_per_lap2": state.degradation_acceleration_s_per_lap2,
                                "tyre_cliff_probability": state.tyre_cliff_probability,
                                "remaining_tyre_life_laps": state.remaining_tyre_life_laps,
                                "strategy_decision": decision.decision.value,
                                "strategy_confidence": decision.confidence,
                                "reasons": decision.reasons,
                                "risks": decision.risks,
                                "invalidation_conditions": decision.invalidation_conditions,
                            }
                            await websocket.send_json(msg)

                    replay_task = asyncio.create_task(_run_replay(circuit, driver))
                elif action == "stop_replay":
                    if replay_task and not replay_task.done():
                        replay_task.cancel()
                    await websocket.send_json({"type": "REPLAY_STOPPED"})
            except Exception:
                pass
    except WebSocketDisconnect:
        if replay_task and not replay_task.done():
            replay_task.cancel()
        manager.disconnect(websocket)

