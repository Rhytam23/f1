"""
Global configuration for DegradIQ pipeline.
"""
import os

# Determinism
RANDOM_STATE = 42

# Data Filtering
MIN_TYRE_LIFE = 4
YEAR = 2023  # Target year for FastF1 data
CIRCUITS = ['Bahrain', 'Spain', 'Monza']

# Physics Constants
FUEL_BURN_KG_PER_LAP = 1.9
FUEL_TIME_PENALTY_S_PER_KG = 0.03
FUEL_CORRECTION_S_PER_LAP = FUEL_BURN_KG_PER_LAP * FUEL_TIME_PENALTY_S_PER_KG

# Traffic Baseline
TRAFFIC_THRESHOLD_S = 1.5

# Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_CACHE_DIR = os.path.join(BASE_DIR, 'data_cache')
