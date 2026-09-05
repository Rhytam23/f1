import pandas as pd
import numpy as np
from degradiq.ingest import ingest_practice_data, ingest_race_data
from degradiq.pipeline import run_pipeline, apply_defuel, apply_detraffic, get_lap_seconds
from degradiq.model import fit_degradation

target_cases = [
    ('Spain', 'MEDIUM'),
    ('Monza', 'HARD'),
    ('Bahrain', 'SOFT')
]

for circuit, compound in target_cases:
    print(f"\\n========================================")
    print(f"Sanity Check for {circuit} {compound}")
    print(f"========================================")
    
    p_df = ingest_practice_data(circuit)
    r_df = ingest_race_data(circuit)
    
    c_df = run_pipeline(p_df)
    models = fit_degradation(c_df)
    model_info = models.get(compound)
    
    if not model_info or model_info['status'] == "below isolation threshold":
        print("Model not fitted or below threshold.")
        continue
        
    model = model_info['model']
    
    race_clean = apply_defuel(r_df)
    race_clean = apply_detraffic(race_clean)
    race_clean = race_clean.dropna(subset=['DefueledLapTime'])
    race_comp = race_clean[race_clean['Compound'] == compound].copy()
    
    total_laps = 0
    stints_info = []
    
    valid_stints = []
    
    for (driver, stint), group in race_comp.groupby(['DriverNumber', 'Stint']):
        group = group.sort_values('TyreLife')
        if len(group) < 3:
            continue
            
        lap2_row = group.iloc[1]
        lap2_life = lap2_row['TyreLife']
        lap2_actual_time = get_lap_seconds(lap2_row['DefueledLapTime'])
        lap2_pred = model.predict(np.array([[lap2_life]]))[0]
        
        X_test = group[['TyreLife']].values
        y_pred = model.predict(X_test)
        y_pred_baselined = y_pred - lap2_pred
        
        y_actual = get_lap_seconds(group['DefueledLapTime']).values
        y_actual_baselined = y_actual - lap2_actual_time
        
        mae = np.mean(np.abs(y_pred_baselined - y_actual_baselined))
        
        total_laps += len(group)
        min_life = group['TyreLife'].min()
        max_life = group['TyreLife'].max()
        
        stints_info.append({
            'driver': driver,
            'stint': stint,
            'laps': len(group),
            'min_life': min_life,
            'max_life': max_life,
            'mae': mae
        })
        
        for i in range(len(group)):
            valid_stints.append({
                'Driver': driver,
                'Stint': stint,
                'TyreLife': X_test[i][0],
                'ActualDelta': y_actual_baselined[i],
                'PredDelta': y_pred_baselined[i]
            })
            
    print(f"Total valid race laps for MAE: {total_laps}")
    print(f"Number of valid stints: {len(stints_info)}")
    
    if stints_info:
        longest = max(stints_info, key=lambda x: x['laps'])
        print(f"\\nLongest continuous stint:")
        print(f"  Driver {longest['driver']} Stint {longest['stint']}: {longest['laps']} laps (Tyre age {longest['min_life']} to {longest['max_life']}), MAE: {longest['mae']:.2f}s")
        
        avg_stint_len = np.mean([s['laps'] for s in stints_info])
        min_age = min([s['min_life'] for s in stints_info])
        max_age = max([s['max_life'] for s in stints_info])
        print(f"\\nStint Summary:")
        print(f"  Average stint length: {avg_stint_len:.1f} laps")
        print(f"  Overall tyre age range covered: {min_age} to {max_age} laps")
        
        print(f"\\nExample rows from longest stint (Driver {longest['driver']}):")
        example_rows = [r for r in valid_stints if r['Driver'] == longest['driver'] and r['Stint'] == longest['stint']]
        target_ages = [4.0, 9.0, 15.0, 26.0, 38.0]
        selected_rows = []
        for age in target_ages:
            # find closest row
            closest = None
            min_diff = float('inf')
            for r in example_rows:
                diff = abs(r['TyreLife'] - age)
                if diff < min_diff and diff <= 2.0: # within 2 laps
                    min_diff = diff
                    closest = r
            if closest and closest not in selected_rows:
                selected_rows.append(closest)
                
        if not selected_rows:
            indices = np.linspace(0, len(example_rows)-1, min(4, len(example_rows)), dtype=int)
            selected_rows = [example_rows[idx] for idx in indices]
            
        print(f"  {'TyreLife':<10} | {'Actual Delta':<15} | {'Predicted Delta':<15} | {'Error':<10}")
        print(f"  " + "-"*60)
        for row in selected_rows:
            error = abs(row['ActualDelta'] - row['PredDelta'])
            print(f"  {row['TyreLife']:<10.1f} | {row['ActualDelta']:<15.3f} | {row['PredDelta']:<15.3f} | {error:<10.3f}")
