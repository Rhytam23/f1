import pandas as pd
from degradiq.ingest import ingest_race_data
from degradiq.pipeline import apply_defuel, get_lap_seconds

circuit = 'Bahrain'
print(f"\\n--- {circuit} ---")
r_laps = ingest_race_data(circuit)
print(f"Total race laps after ingest filter: {len(r_laps)}")

r_clean = apply_defuel(r_laps)
nans = r_clean['DefueledLapTime'].isna().sum()
print(f"Number of NaNs in DefueledLapTime: {nans}")

# Let's see if dropping NaNs fixes the MAE issue
for (driver, stint), group in r_clean.groupby(['DriverNumber', 'Stint']):
    group = group.dropna(subset=['DefueledLapTime'])
    if len(group) >= 3:
        pass
print("Done.")
