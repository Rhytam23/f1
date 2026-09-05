"""
Ingest module for DegradIQ.
Fetches practice data from FastF1 and applies initial filtering.
"""
import os
import fastf1
import pandas as pd
from degradiq.config import MIN_TYRE_LIFE, YEAR, DATA_CACHE_DIR

def setup_cache():
    """Ensure FastF1 cache is enabled and directory exists."""
    os.makedirs(DATA_CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(DATA_CACHE_DIR)

def load_session_laps(circuit: str, session_name: str) -> pd.DataFrame:
    """
    Load laps for a given circuit and session (e.g., 'FP1', 'FP2', 'FP3', 'R').
    """
    setup_cache()
    try:
        session = fastf1.get_session(YEAR, circuit, session_name)
        session.load(telemetry=False, weather=True, messages=False)
        laps = session.laps
        return laps
    except Exception as e:
        print(f"Error loading {circuit} {session_name}: {e}")
        return pd.DataFrame()

def ingest_practice_data(circuit: str) -> pd.DataFrame:
    """
    Load FP1, FP2, and FP3 for a circuit, combine, and apply initial filters.
    """
    all_laps = []
    for session_name in ['FP1', 'FP2', 'FP3']:
        laps = load_session_laps(circuit, session_name)
        if not laps.empty:
            laps['Session'] = session_name
            all_laps.append(laps)
            
    if not all_laps:
        print(f"No practice data found for {circuit}")
        return pd.DataFrame()
        
    combined = pd.concat(all_laps, ignore_index=True)
    
    # Apply TyreLife filter
    initial_count = len(combined)
    
    # FastF1 tyre life column is 'TyreLife'
    # Drop rows where TyreLife is missing or less than MIN_TYRE_LIFE
    filtered = combined.dropna(subset=['TyreLife'])
    filtered = filtered[filtered['TyreLife'] >= MIN_TYRE_LIFE]
    
    final_count = len(filtered)
    print(f"[{circuit}] Practice Laps - Initial: {initial_count}, After TyreLife>={MIN_TYRE_LIFE} filter: {final_count}")
    
    return filtered

def ingest_race_data(circuit: str) -> pd.DataFrame:
    """
    Load Race session data for holdout validation.
    """
    laps = load_session_laps(circuit, 'R')
    if laps.empty:
        return laps
        
    initial_count = len(laps)
    filtered = laps.dropna(subset=['TyreLife'])
    filtered = filtered[filtered['TyreLife'] >= MIN_TYRE_LIFE]
    final_count = len(filtered)
    
    print(f"[{circuit}] Race Laps - Initial: {initial_count}, After TyreLife>={MIN_TYRE_LIFE} filter: {final_count}")
    return filtered
    
if __name__ == '__main__':
    # Simple verification script for Phase 1
    from degradiq.config import CIRCUITS
    
    print("Testing DegradIQ Ingest (Phase 1)...\\n")
    for c in CIRCUITS:
        print(f"--- Fetching {c} ---")
        p_laps = ingest_practice_data(c)
        if not p_laps.empty:
             print(f"Successfully loaded {len(p_laps)} valid practice laps for {c}.\\n")
