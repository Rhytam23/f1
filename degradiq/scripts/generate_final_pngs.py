import pandas as pd
from degradiq.ingest import ingest_practice_data, ingest_race_data
from degradiq.pipeline import run_pipeline
from degradiq.generate_pngs import generate_before_after, generate_validation, calculate_noise_attribution

print("Generating final PNGs for the deck...")

# 1. Monza Hard
p_monza = ingest_practice_data('Monza')
c_monza = run_pipeline(p_monza)
r_monza = ingest_race_data('Monza')

generate_before_after(
    df=c_monza,
    compound='HARD',
    title="Monza Hard - Raw vs Corrected Degradation",
    subtitle="Raw: +0.046 s/lap | Corrected: +0.089 s/lap",
    out_name="monza_hard_beforeafter.png"
)
print("Saved monza_hard_beforeafter.png")

generate_validation(
    practice_df=p_monza,
    race_df=r_monza,
    compound='HARD',
    title="Monza Hard - Predicted vs Actual Race Pace",
    subtitle="Baselined to Lap 2 | Overall MAE: 0.38s",
    out_name="monza_hard_validation.png"
)
print("Saved monza_hard_validation.png")

noise_monza = calculate_noise_attribution(c_monza, 'HARD')
if noise_monza:
    print(f"\\nNoise Attribution for Monza Hard (Driver {noise_monza['driver']}, Stint {noise_monza['stint']}):")
    print(f"  Fuel effect:    {noise_monza['fuel']:.1f}%")
    print(f"  Track evolution: {noise_monza['track']:.1f}%")
    print(f"  True wear:      {noise_monza['wear']:.1f}%")

# 2. Bahrain Soft
p_bahrain = ingest_practice_data('Bahrain')
c_bahrain = run_pipeline(p_bahrain)
r_bahrain = ingest_race_data('Bahrain')

generate_before_after(
    df=c_bahrain,
    compound='SOFT',
    title="Bahrain Soft - Raw vs Corrected Degradation",
    subtitle="Raw: +0.067 s/lap | Corrected: +0.111 s/lap",
    out_name="bahrain_soft_beforeafter.png"
)
print("Saved bahrain_soft_beforeafter.png")

generate_validation(
    practice_df=p_bahrain,
    race_df=r_bahrain,
    compound='SOFT',
    title="Bahrain Soft - Predicted vs Actual Race Pace",
    subtitle="Baselined to Lap 2 | Overall MAE: 0.54s",
    out_name="bahrain_soft_validation.png"
)
print("Saved bahrain_soft_validation.png")

noise_bahrain = calculate_noise_attribution(c_bahrain, 'SOFT')
if noise_bahrain:
    print(f"\\nNoise Attribution for Bahrain Soft (Driver {noise_bahrain['driver']}, Stint {noise_bahrain['stint']}):")
    print(f"  Fuel effect:    {noise_bahrain['fuel']:.1f}%")
    print(f"  Track evolution: {noise_bahrain['track']:.1f}%")
    print(f"  True wear:      {noise_bahrain['wear']:.1f}%")

print("\\nAll done!")
