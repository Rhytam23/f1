import pandas as pd
from degradiq.ingest import ingest_practice_data
from degradiq.pipeline import run_pipeline
from degradiq.generate_pngs import calculate_noise_attribution

target_cases = [
    ('Bahrain', 'HARD'),
    ('Bahrain', 'MEDIUM'),
    ('Bahrain', 'SOFT'),
    ('Spain', 'MEDIUM'),
    ('Monza', 'HARD'),
    ('Monza', 'MEDIUM')
]

print("Calculating Noise Attribution for specific cases...")

for circuit, compound in target_cases:
    # We only need practice data to calculate noise attribution for the model's training data
    p_df = ingest_practice_data(circuit)
    c_df = run_pipeline(p_df)
    
    noise = calculate_noise_attribution(c_df, compound)
    if noise:
        print(f"\\n[{circuit} - {compound}] (Driver {noise['driver']}, Stint {noise['stint']}):")
        print(f"  Fuel effect:    {noise['fuel']:>5.1f}%")
        print(f"  Track evolution: {noise['track']:>5.1f}%")
        print(f"  True wear:      {noise['wear']:>5.1f}%")
    else:
        print(f"\\n[{circuit} - {compound}]: No valid practice stints found to attribute noise.")
