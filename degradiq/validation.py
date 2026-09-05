import pandas as pd
import numpy as np
from degradiq.pipeline import run_pipeline, get_lap_seconds
from degradiq.model import fit_degradation

def validate_circuit(practice_df: pd.DataFrame, race_df: pd.DataFrame):
    """
    Runs the pipeline, fits the model, and validates against race data.
    Returns a dict with metrics per compound.
    """
    if practice_df.empty or race_df.empty:
        return {}
        
    # 1. Clean practice and fit
    clean_practice = run_pipeline(practice_df)
    models = fit_degradation(clean_practice)
    
    # 2. Validate on race
    from degradiq.pipeline import apply_defuel, apply_detraffic
    race_clean = apply_defuel(race_df)
    race_clean = apply_detraffic(race_clean)
    race_clean = race_clean.dropna(subset=['DefueledLapTime'])
    
    results = {}
    
    for compound, model_info in models.items():
        status = model_info['status']
        p_laps_count = len(clean_practice[clean_practice['Compound'] == compound])
        
        results[compound] = {
            'slope_clean': model_info['slope_clean'],
            'slope_raw': model_info['slope_raw'],
            'multiplier': model_info['multiplier'],
            'status': status,
            'p_laps': p_laps_count,
            'r_laps': 0,
            'mae': None
        }
        
        if status == "below isolation threshold":
            continue
            
        model = model_info['model']
        maes = []
        r_laps_count = 0
        
        race_comp = race_clean[race_clean['Compound'] == compound]
        
        for (driver, stint), group in race_comp.groupby(['DriverNumber', 'Stint']):
            group = group.sort_values('TyreLife')
            if len(group) < 3:
                continue
                
            r_laps_count += len(group)
            
            # Find lap 2 of the stint
            lap2_row = group.iloc[1]
            lap2_life = lap2_row['TyreLife']
            lap2_actual_time = get_lap_seconds(lap2_row['DefueledLapTime'])
            
            lap2_pred = model.predict(np.array([[lap2_life]]))[0]
            
            # Baseline
            X_test = group[['TyreLife']].values
            y_pred = model.predict(X_test)
            y_pred_baselined = y_pred - lap2_pred
            
            y_actual = get_lap_seconds(group['DefueledLapTime']).values
            y_actual_baselined = y_actual - lap2_actual_time
            
            stint_mae = np.mean(np.abs(y_pred_baselined - y_actual_baselined))
            maes.append(stint_mae)
            
        results[compound]['r_laps'] = r_laps_count
        if maes:
            results[compound]['mae'] = np.mean(maes)
            
    return results
