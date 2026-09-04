"""Unit and interface tests for data acquisition and provenance handling."""

from __future__ import annotations

import os
from datetime import datetime, timezone
import pytest

from data.schemas.provenance import DataClassification, LapQuality
from data.loaders.fastf1_loader import parse_compound, FastF1SessionDescriptor
from backend.telemetry.schema import TyreCompound, DataSource, RaceTelemetry


def test_data_classification_enum():
    assert DataClassification.REAL_TELEMETRY == "REAL_TELEMETRY"
    assert DataClassification.HISTORICAL_REPLAY == "HISTORICAL_REPLAY"
    assert LapQuality.CLEAN == "CLEAN"


def test_parse_compound():
    assert parse_compound("SOFT") == TyreCompound.SOFT
    assert parse_compound("MEDIUM") == TyreCompound.MEDIUM
    assert parse_compound("HARD") == TyreCompound.HARD
    assert parse_compound("INTERMEDIATE") == TyreCompound.INTERMEDIATE
    assert parse_compound("WET") == TyreCompound.WET
    assert parse_compound(None) == TyreCompound.UNKNOWN


def test_session_descriptor():
    desc = FastF1SessionDescriptor(
        season=2023,
        circuit="Silverstone",
        session_type="R",
        driver="VER",
    )
    assert desc.season == 2023
    assert desc.circuit == "Silverstone"
    assert desc.data_classification == DataClassification.REAL_TELEMETRY


def test_race_telemetry_provenance_extra():
    frame = RaceTelemetry(
        source=DataSource.REAL_CAR,
        source_timestamp=datetime.now(timezone.utc),
        car_id="VER",
        lap=1,
        speed_kph=315.0,
        data_classification=DataClassification.REAL_TELEMETRY,
        circuit="Silverstone",
    )
    assert frame.car_id == "VER"
    assert frame.speed_kph == 315.0
    assert frame.data_classification == DataClassification.REAL_TELEMETRY
    assert frame.circuit == "Silverstone"
