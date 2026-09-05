"""
Verification script to check output against expected results.
"""
from degradiq.config import CIRCUITS
from degradiq.ingest import ingest_practice_data, ingest_race_data
from degradiq.validation import validate_circuit

def run_verification():
    for circuit in CIRCUITS:
        print(f"\\n{'='*40}")
        print(f"Running DegradIQ Verification for {circuit}")
        print(f"{'='*40}")
        
        p_laps = ingest_practice_data(circuit)
        r_laps = ingest_race_data(circuit)
        
        results = validate_circuit(p_laps, r_laps)
        
        if not results:
            print(f"{circuit}: No models fitted.")
            continue
            
        for compound, info in results.items():
            status = info['status']
            p_laps = info['p_laps']
            r_laps = info['r_laps']
            mae = info['mae']
            
            if status == "below isolation threshold":
                mae_str = f"{mae:.2f}s" if mae is not None else "N/A"
                print(f"  {compound}: below isolation threshold | P-Laps: {p_laps} | R-Laps: {r_laps} | MAE: {mae_str}")
            else:
                slope_clean = info['slope_clean']
                slope_raw = info['slope_raw']
                mult = info['multiplier']
                mae_str = f"{mae:.2f}s" if mae is not None else "N/A"
                print(f"  {compound}: Raw: +{slope_raw:.3f} s/lap | Corrected: +{slope_clean:.3f} s/lap ({mult:.1f}x) | P-Laps: {p_laps} | R-Laps: {r_laps} | MAE: {mae_str}")
                
if __name__ == '__main__':
    run_verification()
