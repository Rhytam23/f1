import pandas as pd
import numpy as np
from scipy.optimize import curve_fit

class HingeModel:
    def __init__(self):
        self.popt = None
        
    def model_func(self, x, b, w1, w2, w3, k1, k2):
        return b + w1 * x + w2 * np.maximum(0, x - k1) + w3 * np.maximum(0, x - k2)
        
    def fit(self, X, y):
        if len(X.shape) > 1: X = X.flatten()
        max_x = np.max(X)
        if max_x < 10:
            slope, intercept = np.polyfit(X, y, 1)
            self.popt = [intercept, max(0, slope), 0, 0, max_x/3, max_x*2/3]
            return
            
        p0 = [np.mean(y[:5]), 0.0, 0.05, 0.1, max_x*0.33, max_x*0.66]
        bounds = (
            [-np.inf, 0, 0, 0, 2, 3],
            [np.inf, np.inf, np.inf, np.inf, max_x-2, max_x-1]
        )
        try:
            self.popt, _ = curve_fit(self.model_func, X, y, p0=p0, bounds=bounds, maxfev=10000)
        except Exception:
            slope, intercept = np.polyfit(X, y, 1)
            self.popt = [intercept, max(0, slope), 0, 0, max_x*0.33, max_x*0.66]
            
    def predict(self, X):
        if len(X.shape) > 1: X = X.flatten()
        return self.model_func(X, *self.popt)

def fit_degradation(df: pd.DataFrame):
    """
    Fit Hinge Model per compound on the cleaned residual.
    Clamp wear slope to >= 0, else report 'below isolation threshold'.
    Calculates noise attribution.
    """
    results = {}
    
    if df.empty or 'Compound' not in df.columns:
        return results
        
    for compound, group in df.groupby('Compound'):
        if len(group) < 10:
            continue
            
        X = group[['TyreLife']].values
        y_clean = group['CleanedLapTime'].values
        
        # Get raw lap times for multiplier calculation
        y_raw = group['LapTime'].dt.total_seconds().values if pd.api.types.is_timedelta64_dtype(group['LapTime']) else group['LapTime'].values
        
        # Fit models
        model_clean = HingeModel()
        model_clean.fit(X, y_clean)
        
        model_raw = HingeModel()
        model_raw.fit(X, y_raw)
        
        # Calculate slope (linear approx over the tyre life range)
        life_min, life_max = int(group['TyreLife'].min()), int(group['TyreLife'].max())
        if life_max <= life_min:
            continue
            
        pred_clean = model_clean.predict(np.array([[life_min], [life_max]]))
        slope_clean = (pred_clean[1] - pred_clean[0]) / (life_max - life_min)
        
        pred_raw = model_raw.predict(np.array([[life_min], [life_max]]))
        slope_raw = (pred_raw[1] - pred_raw[0]) / (life_max - life_min)
        
        # Clamping
        status = "ok"
        if slope_clean <= 0:
            status = "below isolation threshold"
            slope_clean = 0.0
        elif slope_clean > 0.22:
            slope_clean = 0.22
            
        # Multiplier vs raw
        multiplier = slope_clean / slope_raw if slope_raw > 0 else 0
        if status == "below isolation threshold":
            multiplier = 0.0
            
        results[compound] = {
            'model': model_clean,
            'slope_clean': slope_clean,
            'slope_raw': slope_raw,
            'multiplier': multiplier,
            'status': status
        }
        
    return results
