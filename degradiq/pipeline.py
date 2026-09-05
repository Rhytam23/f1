import pandas as pd
import numpy as np
from degradiq.config import FUEL_CORRECTION_S_PER_LAP, TRAFFIC_THRESHOLD_S

def get_lap_seconds(series):
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return series

def apply_defuel(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    lap_secs = get_lap_seconds(df['LapTime'])
    fuel_penalty = (df['LapNumber'] - 1) * FUEL_CORRECTION_S_PER_LAP
    df['DefueledLapTime'] = lap_secs + fuel_penalty
    return df

def apply_detraffic(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['StintMedian'] = df.groupby(['DriverNumber', 'Stint'])['DefueledLapTime'].transform('median')
    mask = df['DefueledLapTime'] <= (df['StintMedian'] + TRAFFIC_THRESHOLD_S)
    filtered_df = df[mask].copy()
    filtered_df.drop(columns=['StintMedian'], inplace=True)
    return filtered_df

def apply_deevolve(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
        
    df = df.copy()
    # 1. Estimate field-wide track evolution trend
    # Use Session time (converted to minutes) to track evolution across the whole field.
    # Grouping by LapNumber conflates track evolution with tyre degradation.
    df['SessionMinutes'] = df['Time'].dt.total_seconds() / 60.0
    
    # We fit a linear trend across the whole field against SessionMinutes
    # Drop NaNs just in case
    valid_times = df.dropna(subset=['SessionMinutes', 'DefueledLapTime'])
    if len(valid_times) > 1:
        slope, intercept = np.polyfit(valid_times['SessionMinutes'], valid_times['DefueledLapTime'], 1)
        # Track evolution means track gets FASTER, so lap times get lower (negative slope).
        # If slope is positive, it's an artifact of drivers switching to high-fuel long runs later in the session.
        # We cap track evolution slope at 0 (meaning track doesn't get worse).
        if slope > 0:
            slope = 0
    else:
        slope = 0
        
    # The expected evolution improvement for a given lap vs lap 1 (which we'll proxy by start of stint)
    # Wait, the spec: "subtract it lap by lap". 
    # Let's calculate the expected time gained since the start of the session
    evolution_delta = df['SessionMinutes'] * slope
    
    # We want to subtract the evolution improvement.
    # If slope is negative, evolution_delta is negative (faster).
    # To remove the effect, we subtract it (which means subtracting a negative -> adding time)
    # So we want to subtract evolution_delta from DefueledLapTime.
    df['EvolutionDelta'] = -evolution_delta # positive value representing time to add back
    
    # 2. Cap the correction per stint
    stint_ranges = df.groupby(['DriverNumber', 'Stint'])['LapTime'].apply(
        lambda x: get_lap_seconds(x).max() - get_lap_seconds(x).min()
    ).to_dict()
    
    def cap_evolution(row):
        stint_key = (row['DriverNumber'], row['Stint'])
        stint_range = stint_ranges.get(stint_key, 0)
        delta = row['EvolutionDelta']
        if delta > 0:
            return min(delta, stint_range)
        else:
            return max(delta, -stint_range)
            
    df['CappedEvolutionDelta'] = df.apply(cap_evolution, axis=1)
    
    # 3. Apply the correction
    df['CleanedLapTime'] = df['DefueledLapTime'] + df['CappedEvolutionDelta']
    
    return df

def run_pipeline(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = apply_defuel(df)
    df = apply_detraffic(df)
    df = apply_deevolve(df)
    return df
