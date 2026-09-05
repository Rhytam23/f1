import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from degradiq.ingest import ingest_practice_data, ingest_race_data
from degradiq.pipeline import run_pipeline, apply_defuel, apply_detraffic, get_lap_seconds
from degradiq.model import fit_degradation
from degradiq.scripts.generate_pngs import calculate_noise_attribution

st.set_page_config(page_title="DegradeIQ Dashboard", layout="wide", initial_sidebar_state="collapsed")

st.title("DegradeIQ — isolating true tyre wear from F1 practice data")
st.markdown("---")

@st.cache_data
def load_circuit_data(circuit):
    p_df = ingest_practice_data(circuit)
    r_df = ingest_race_data(circuit)
    c_df = run_pipeline(p_df)
    models = fit_degradation(c_df)
    return p_df, r_df, c_df, models

# 1. Circuit + Compound Selector
col1, col2 = st.columns(2)
with col1:
    circuit = st.selectbox("Select Circuit", ["Monza", "Bahrain", "Spain"], index=0)

p_df, r_df, c_df, models = load_circuit_data(circuit)
available_compounds = [comp for comp, info in models.items() if info['status'] != "below isolation threshold"]
if not available_compounds:
    st.error("No valid models found for this circuit.")
    st.stop()

# Default to Monza Hard if available
default_idx = 0
if circuit == "Monza" and "HARD" in available_compounds:
    default_idx = available_compounds.index("HARD")

with col2:
    compound = st.selectbox("Select Compound", available_compounds, index=default_idx)

model_info = models[compound]
model = model_info['model']
slope_clean = model_info['slope_clean']
slope_raw = model_info['slope_raw']

st.markdown("### Raw vs Corrected Degradation")

# 2. Before/After Panel
comp_df = c_df[c_df['Compound'] == compound].copy()
X = comp_df['TyreLife'].values
y_clean = comp_df['CleanedLapTime'].values
y_raw = get_lap_seconds(comp_df['LapTime']).values

x_range = np.array([X.min(), X.max()])
slope_raw_fit, int_raw = np.polyfit(X, y_raw, 1)
slope_clean_fit, int_clean = np.polyfit(X, y_clean, 1)

fig_ba = go.Figure()

fig_ba.add_trace(go.Scatter(
    x=X, y=y_raw, mode='markers', name='Raw Laps',
    marker=dict(color='lightcoral', size=8, opacity=0.5)
))
fig_ba.add_trace(go.Scatter(
    x=x_range, y=slope_raw_fit * x_range + int_raw, mode='lines', name=f'Raw Trend (+{slope_raw:.3f} s/lap)',
    line=dict(color='red', width=3, dash='dash')
))

fig_ba.add_trace(go.Scatter(
    x=X, y=y_clean, mode='markers', name='Corrected Laps',
    marker=dict(color='dodgerblue', size=8, opacity=0.7)
))
fig_ba.add_trace(go.Scatter(
    x=x_range, y=slope_clean_fit * x_range + int_clean, mode='lines', name=f'Corrected Trend (+{slope_clean:.3f} s/lap)',
    line=dict(color='blue', width=3)
))

fig_ba.update_layout(
    xaxis_title='Tyre Life (Laps)',
    yaxis_title='Lap Time (s)',
    hovermode='x',
    template='plotly_white',
    height=500
)
st.plotly_chart(fig_ba, use_container_width=True)


# 3. Noise Attribution
st.markdown("### Noise Attribution")
noise = calculate_noise_attribution(c_df, compound)

if noise:
    st.write(f"Breakdown for longest {compound} practice stint (Driver {noise['driver']}, Stint {noise['stint']}):")
    
    fig_noise = go.Figure(go.Bar(
        x=[noise['fuel'], noise['track'], noise['wear']],
        y=['Fuel Effect', 'Track Evolution', 'True Wear'],
        orientation='h',
        marker=dict(color=['#f39c12', '#2ecc71', '#3498db']),
        text=[f"{noise['fuel']:.1f}%", f"{noise['track']:.1f}%", f"{noise['wear']:.1f}%"],
        textposition='auto'
    ))
    fig_noise.update_layout(
        barmode='stack', 
        height=250, 
        xaxis_title='Percentage of Lap Time Variance (%)',
        template='plotly_white'
    )
    st.plotly_chart(fig_noise, use_container_width=True)
else:
    st.write("Could not compute noise attribution for this stint.")


# 4. Validation Panel
st.markdown("### Predicted vs Actual Race Pace")

@st.cache_data
def compute_validation(_r_df, _model, compound):
    race_clean = apply_defuel(_r_df)
    race_clean = apply_detraffic(race_clean)
    race_clean = race_clean.dropna(subset=['DefueledLapTime'])
    race_comp = race_clean[race_clean['Compound'] == compound].copy()
    
    maes = []
    stints_info = []
    
    for (driver, stint), group in race_comp.groupby(['DriverNumber', 'Stint']):
        group = group.sort_values('TyreLife')
        if len(group) < 3:
            continue
            
        lap2_row = group.iloc[1]
        lap2_life = lap2_row['TyreLife']
        lap2_actual_time = get_lap_seconds(lap2_row['DefueledLapTime'])
        lap2_pred = _model.predict(np.array([[lap2_life]]))[0]
        
        X_test = group[['TyreLife']].values
        y_pred = _model.predict(X_test)
        y_pred_baselined = y_pred - lap2_pred
        
        y_actual = get_lap_seconds(group['DefueledLapTime']).values
        y_actual_baselined = y_actual - lap2_actual_time
        
        stint_mae = np.mean(np.abs(y_pred_baselined - y_actual_baselined))
        maes.append(stint_mae)
        
        stints_info.append({
            'driver': driver,
            'stint': stint,
            'laps': len(group),
            'X': X_test.flatten(),
            'y_actual': y_actual_baselined,
            'y_pred': y_pred_baselined
        })
        
    overall_mae = np.mean(maes) if maes else None
    return overall_mae, stints_info

overall_mae, stints_info = compute_validation(r_df, model, compound)

col_val1, col_val2 = st.columns([1, 3])
with col_val1:
    if overall_mae is not None:
        st.metric("Overall Validation MAE", f"{overall_mae:.2f}s", "Baselined to Lap 2", delta_color="off")
    else:
        st.metric("Overall Validation MAE", "N/A")
    st.write(f"Validated across {len(stints_info)} race stints.")

with col_val2:
    if stints_info:
        longest = max(stints_info, key=lambda x: x['laps'])
        fig_val = go.Figure()
        
        fig_val.add_trace(go.Scatter(
            x=longest['X'], y=longest['y_actual'], mode='markers', name='Actual Race Laps (Baselined)',
            marker=dict(color='black', size=10)
        ))
        fig_val.add_trace(go.Scatter(
            x=longest['X'], y=longest['y_pred'], mode='lines', name='Predicted Degradation Shape',
            line=dict(color='green', width=4)
        ))
        
        fig_val.update_layout(
            title=f"Longest Stint: Driver {longest['driver']} (Stint {longest['stint']})",
            xaxis_title='Tyre Life (Laps)',
            yaxis_title='Delta to Lap 2 (s)',
            hovermode='x',
            template='plotly_white',
            height=400
        )
        # add 0 line
        fig_val.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        st.plotly_chart(fig_val, use_container_width=True)
    else:
        st.write("No valid race laps to display validation.")


# 5. Pit Window Recommendation
st.markdown("### Pit-Window Recommendation")

# Generate degradation curve up to 60 laps
test_laps = np.arange(1, 61).reshape(-1, 1)
pred_deg = model.predict(test_laps)
# Baseline to lap 1
pred_deg = pred_deg - pred_deg[0]

# Define thresholds for pit window (e.g. losing 1.5s to 2.5s per lap)
thresh_low = 1.5
thresh_high = 2.5

window_start = None
window_end = None

for i, deg in enumerate(pred_deg):
    lap = test_laps[i][0]
    if deg >= thresh_low and window_start is None:
        window_start = int(lap)
    if deg >= thresh_high and window_end is None:
        window_end = int(lap)

if window_start is None:
    st.success("This tyre can easily go to the end of a typical stint without massive degradation (stays under 1.5s delta).")
else:
    if window_end is None:
        window_end = 60
    st.info(f"**Optimal Pit Window:** Laps {window_start} - {window_end}")
    st.write(f"*(Recommendation based on tyre reaching {thresh_low}s - {thresh_high}s of degradation)*")
