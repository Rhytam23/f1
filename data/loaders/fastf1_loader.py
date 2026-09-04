"""FastF1 Data Loader and RaceTelemetry converter for RacePulse."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from pydantic import BaseModel

from backend.telemetry.schema import (
    DataSource,
    PitStatus,
    RaceTelemetry,
    TrackState,
    TyreCompound,
    WeatherState,
)
from data.schemas.provenance import DataClassification, LapQuality


class FastF1SessionDescriptor(BaseModel):
    season: int
    circuit: str
    session_type: str  # 'R', 'Q', 'FP1', 'FP2', 'FP3'
    driver: str  # e.g., 'VER', 'HAM', 'NOR'
    data_classification: DataClassification = DataClassification.REAL_TELEMETRY


def parse_compound(compound_str: Optional[str]) -> TyreCompound:
    if not compound_str or pd.isna(compound_str):
        return TyreCompound.UNKNOWN
    c = str(compound_str).upper()
    if "SOFT" in c:
        return TyreCompound.SOFT
    if "MEDIUM" in c:
        return TyreCompound.MEDIUM
    if "HARD" in c:
        return TyreCompound.HARD
    if "INTERMEDIATE" in c:
        return TyreCompound.INTERMEDIATE
    if "WET" in c:
        return TyreCompound.WET
    return TyreCompound.UNKNOWN


def load_fastf1_session_telemetry(
    season: int,
    circuit: str,
    session_type: str = "R",
    driver: str = "VER",
    cache_dir: str = "data/cache",
) -> List[RaceTelemetry]:
    """Loads FastF1 session data and returns a list of RaceTelemetry frames."""
    import fastf1

    os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

    session = fastf1.get_session(season, circuit, session_type)
    session.load(telemetry=True, laps=True, weather=True)

    driver_laps = session.laps.pick_driver(driver)
    if driver_laps.empty:
        return []

    telemetry_frames: List[RaceTelemetry] = []
    seq_id = 1

    for _, lap in driver_laps.iterrows():
        try:
            lap_num = int(lap["LapNumber"])
            compound = parse_compound(lap.get("Compound"))
            tyre_age = int(lap.get("TyreLife", 1)) if not pd.isna(lap.get("TyreLife")) else 1
            pit_out = not pd.isna(lap.get("PitOutTime"))
            pit_in = not pd.isna(lap.get("PitInTime"))

            pit_stat = PitStatus.ON_TRACK
            if pit_in:
                pit_stat = PitStatus.ENTERING_PIT
            elif pit_out:
                pit_stat = PitStatus.EXITING_PIT

            # Extract telemetry samples for this lap
            lap_tel = lap.get_telemetry()
            if lap_tel is None or lap_tel.empty:
                continue

            for _, tel in lap_tel.iterrows():
                dt_val = tel.get("Date")
                if pd.isna(dt_val):
                    ts = datetime.now(timezone.utc)
                elif isinstance(dt_val, pd.Timestamp):
                    ts = dt_val.to_pydatetime()
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                else:
                    ts = datetime.now(timezone.utc)

                speed = float(tel["Speed"]) if not pd.isna(tel.get("Speed")) else None
                throttle = float(tel["Throttle"]) if not pd.isna(tel.get("Throttle")) else None
                brake_val = tel.get("Brake")
                brake = (100.0 if brake_val is True else (0.0 if brake_val is False else float(brake_val))) if not pd.isna(brake_val) else 0.0
                rpm = float(tel["RPM"]) if not pd.isna(tel.get("RPM")) else None
                gear = int(tel["nGear"]) if not pd.isna(tel.get("nGear")) else None
                drs_val = int(tel["DRS"]) if not pd.isna(tel.get("DRS")) else 0
                drs_active = drs_val in [10, 12, 14]

                x_pos = float(tel["X"]) if not pd.isna(tel.get("X")) else None
                y_pos = float(tel["Y"]) if not pd.isna(tel.get("Y")) else None
                z_pos = float(tel["Z"]) if not pd.isna(tel.get("Z")) else None
                distance = float(tel["Distance"]) if not pd.isna(tel.get("Distance")) else None

                frame = RaceTelemetry(
                    schema_version="0.1.0",
                    source=DataSource.REAL_CAR,
                    source_timestamp=ts,
                    sequence_id=seq_id,
                    car_id=driver,
                    lap=lap_num,
                    position=int(lap["Position"]) if not pd.isna(lap.get("Position")) else 1,
                    speed_kph=speed,
                    throttle_pct=throttle,
                    brake_pct=brake,
                    gear=gear,
                    rpm=rpm,
                    tyre_compound=compound,
                    tyre_age_laps=tyre_age,
                    fuel_load_kg=max(10.0, 110.0 - lap_num * 1.7),  # Derived linear fuel burn estimate
                    drs_available=bool(drs_val > 0),
                    drs_active=drs_active,
                    pit_status=pit_stat,
                    track_state=TrackState.GREEN,
                    weather=WeatherState.DRY,
                    # Attach real telemetry metadata under model extra
                    data_classification=DataClassification.REAL_TELEMETRY,
                    circuit=circuit,
                    season=season,
                    pos_x=x_pos,
                    pos_y=y_pos,
                    pos_z=z_pos,
                    lap_distance_m=distance,
                )
                telemetry_frames.append(frame)
                seq_id += 1

        except Exception as e:
            continue

    return telemetry_frames
