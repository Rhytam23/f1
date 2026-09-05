import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

from degradiq.ingest import ingest_practice_data, ingest_race_data
from degradiq.pipeline import run_pipeline, apply_defuel, apply_detraffic, get_lap_seconds
from degradiq.validation import validate_circuit

# Setup matplotlib for high-res PNGs
plt.rcParams['figure.figsize'] = (16, 9)
plt.rcParams['figure.dpi'] = 300
plt.rcParams['font.size'] = 18
plt.rcParams['axes.facecolor'] = 'white'
plt.rcParams['figure.facecolor'] = 'white'

def generate_before_after(df, compound, title, subtitle, out_name):
    group = df[df['Compound'] == compound].copy()
    if group.empty:
        return
        
    X = group['TyreLife'].values
    y_clean = group['CleanedLapTime'].values
    y_raw = get_lap_seconds(group['LapTime']).values
    
    # Fit simple linear models for visualization lines
    slope_clean, intercept_clean = np.polyfit(X, y_clean, 1)
    slope_raw, intercept_raw = np.polyfit(X, y_raw, 1)
    
    x_range = np.array([X.min(), X.max()])
    
    fig, ax = plt.subplots()
    
    # Raw Data
    ax.scatter(X, y_raw, color='lightcoral', alpha=0.5, label='Raw Laps')
    ax.plot(x_range, slope_raw * x_range + intercept_raw, color='red', linewidth=3, linestyle='--', label=f'Raw Trend (+{slope_raw:.3f}s/lap)')
    
    # Cleaned Data
    ax.scatter(X, y_clean, color='dodgerblue', alpha=0.7, label='Corrected Laps')
    ax.plot(x_range, slope_clean * x_range + intercept_clean, color='blue', linewidth=3, label=f'Corrected Trend (+{slope_clean:.3f}s/lap)')
    
    ax.set_title(f"{title}\\n{subtitle}", pad=20, fontsize=22, fontweight='bold')
    ax.set_xlabel('Tyre Life (Laps)', fontsize=18)
    ax.set_ylabel('Lap Time (s)', fontsize=18)
    ax.legend(fontsize=16)
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    plt.savefig(out_name, dpi=300)
    plt.close()

def generate_validation(practice_df, race_df, compound, title, subtitle, out_name):
    # Fit model
    from degradiq.model import fit_degradation
    clean_practice = run_pipeline(practice_df)
    models = fit_degradation(clean_practice)
    
    model_info = models.get(compound)
    if not model_info or model_info['status'] == "below isolation threshold":
        return
        
    model = model_info['model']
    
    race_clean = apply_defuel(race_df)
    race_clean = apply_detraffic(race_clean)
    race_clean = race_clean.dropna(subset=['DefueledLapTime'])
    
    race_comp = race_clean[race_clean['Compound'] == compound].copy()
    if race_comp.empty:
        return
        
    fig, ax = plt.subplots()
    
    # Find the longest race stint for visualization
    stints = list(race_comp.groupby(['DriverNumber', 'Stint']))
    if not stints:
        return
    longest_stint = max(stints, key=lambda x: len(x[1]))
    
    group = longest_stint[1].sort_values('TyreLife')
    if len(group) < 3:
        return
        
    lap2_row = group.iloc[1]
    lap2_life = lap2_row['TyreLife']
    lap2_actual_time = get_lap_seconds(lap2_row['DefueledLapTime'])
    lap2_pred = model.predict(np.array([[lap2_life]]))[0]
    
    X_test = group[['TyreLife']].values
    y_pred = model.predict(X_test)
    y_pred_baselined = y_pred - lap2_pred
    
    y_actual = get_lap_seconds(group['DefueledLapTime']).values
    y_actual_baselined = y_actual - lap2_actual_time
    
    ax.scatter(X_test, y_actual_baselined, color='black', label='Actual Race Laps (Baselined)')
    ax.plot(X_test, y_pred_baselined, color='green', linewidth=4, label='Predicted Degradation Shape')
    
    ax.set_title(f"{title}\\n{subtitle}", pad=20, fontsize=22, fontweight='bold')
    ax.set_xlabel('Tyre Life (Laps)', fontsize=18)
    ax.set_ylabel('Delta to Lap 2 (s)', fontsize=18)
    ax.legend(fontsize=16)
    ax.grid(True, alpha=0.3)
    
    # Add a horizontal line at 0 for reference
    ax.axhline(0, color='gray', linestyle='--', alpha=0.5)
    
    fig.tight_layout()
    plt.savefig(out_name, dpi=300)
    plt.close()

def calculate_noise_attribution(clean_df, compound):
    comp_df = clean_df[clean_df['Compound'] == compound].copy()
    # Find the longest stint
    stints = list(comp_df.groupby(['DriverNumber', 'Stint']))
    if not stints:
        return None
        
    longest_stint = max(stints, key=lambda x: len(x[1]))
    stint_df = longest_stint[1].sort_values('TyreLife')
    
    if len(stint_df) < 2:
        return None
        
    # Total changes
    # Fuel changes (which was added back to DefueledLapTime to normalize)
    # The actual fuel effect is what was added.
    fuel_start = (stint_df['LapNumber'].iloc[0] - 1) * 0.057
    fuel_end = (stint_df['LapNumber'].iloc[-1] - 1) * 0.057
    fuel_change = abs(fuel_end - fuel_start)
    
    # Track evolution capped delta
    evo_start = stint_df['CappedEvolutionDelta'].iloc[0]
    evo_end = stint_df['CappedEvolutionDelta'].iloc[-1]
    evo_change = abs(evo_end - evo_start)
    
    # True wear is the cleaned lap time change
    # Using linear fit to get a clean signal of true wear over the stint
    X = stint_df['TyreLife'].values
    Y = stint_df['CleanedLapTime'].values
    slope, intercept = np.polyfit(X, Y, 1)
    wear_change = abs(slope * (X[-1] - X[0]))
    
    total = fuel_change + evo_change + wear_change
    if total == 0:
        return None
        
    return {
        'fuel': (fuel_change / total) * 100,
        'track': (evo_change / total) * 100,
        'wear': (wear_change / total) * 100,
        'driver': longest_stint[0][0],
        'stint': longest_stint[0][1]
    }

if __name__ == '__main__':
    print("Generating PNGs...")
    
    # 1. Spain Medium Before/After
    p_spain = ingest_practice_data('Spain')
    c_spain = run_pipeline(p_spain)
    generate_before_after(
        df=c_spain, 
        compound='MEDIUM', 
        title="Spain Medium - Raw vs Corrected Degradation",
        subtitle="Raw: +0.069 s/lap | Corrected: +0.154 s/lap",
        out_name="spain_medium_beforeafter.png"
    )
    print("Saved spain_medium_beforeafter.png")
    
    # 2. Spain Medium Validation
    r_spain = ingest_race_data('Spain')
    generate_validation(
        practice_df=p_spain,
        race_df=r_spain,
        compound='MEDIUM',
        title="Spain Medium - Predicted vs Actual Race Pace",
        subtitle="Baselined to Lap 2 | MAE: 1.85s",
        out_name="spain_medium_validation.png"
    )
    print("Saved spain_medium_validation.png")
    
    # 3. Monza Hard Before/After
    p_monza = ingest_practice_data('Monza')
    c_monza = run_pipeline(p_monza)
    generate_before_after(
        df=c_monza,
        compound='HARD',
        title="Monza Hard - Raw vs Corrected Degradation",
        subtitle="Raw: +0.032 s/lap | Corrected: +0.077 s/lap",
        out_name="monza_beforeafter.png"
    )
    print("Saved monza_beforeafter.png")
    
    # Noise Attribution
    noise = calculate_noise_attribution(c_spain, 'MEDIUM')
    if noise:
        print(f"\\nNoise Attribution for Spain Medium (Driver {noise['driver']}, Stint {noise['stint']}):")
        print(f"  Fuel effect:    {noise['fuel']:.1f}%")
        print(f"  Track evolution: {noise['track']:.1f}%")
        print(f"  True wear:      {noise['wear']:.1f}%")
    
    print("\\nAll done!")
