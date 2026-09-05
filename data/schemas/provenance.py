"""Data provenance and dataset classification schemas for RacePulse."""

from enum import Enum


class DataClassification(str, Enum):
    REAL_TELEMETRY = "REAL_TELEMETRY"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    DERIVED_FEATURE = "DERIVED_FEATURE"
    PREDICTED_MODEL = "PREDICTED_MODEL"
    CONTROLLED_SIMULATION = "CONTROLLED_SIMULATION"
    UNAVAILABLE = "UNAVAILABLE"


class LapQuality(str, Enum):
    CLEAN = "CLEAN"
    USABLE = "USABLE"
    QUESTIONABLE = "QUESTIONABLE"
    INVALID = "INVALID"
