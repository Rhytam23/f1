import pandas as pd
import numpy as np
from degradiq.ingest import ingest_practice_data
from degradiq.pipeline import apply_defuel, get_lap_seconds

circuit = 'Bahrain'
df = ingest_practice_data(circuit)
df = apply_defuel(df)

# Current Buggy Method
field_trend_lap = df.groupby('LapNumber')['DefueledLapTime'].median().reset_index().dropna()
slope_lap, _ = np.polyfit(field_trend_lap['LapNumber'], field_trend_lap['DefueledLapTime'], 1)
print(f"BUGGY LapNumber Slope (s/lap): {slope_lap:.4f}")

# Using Time
# Time is a timedelta. Let's convert to minutes from start of session
df['SessionMinutes'] = df['Time'].dt.total_seconds() / 60.0
# Bin by 5 minutes to get field median trend
df['TimeBin'] = (df['SessionMinutes'] // 5) * 5
field_trend_time = df.groupby('TimeBin')['DefueledLapTime'].median().reset_index().dropna()
if len(field_trend_time) > 1:
    slope_time, _ = np.polyfit(field_trend_time['TimeBin'], field_trend_time['DefueledLapTime'], 1)
    print(f"Time Slope (s/minute): {slope_time:.4f}")
else:
    print("Not enough time bins.")

# What if we use overall lap index (like an absolute race lap)?
# For practice, there is no absolute lap. Session time is best.

