# Strategy Engine & Intelligence Models

This document presents the mathematical formulations, statistical models, physics decompositions, and optimization algorithms governing intelligence layers and pit strategy choices in TrackShift 2026.

---

## 🛞 1. Tyre Degradation Intelligence

### Physics Pace Decomposition
Observed raw lap time $T_{\text{lap}}(t)$ on lap $t$ is composed of four distinct components:

$$T_{\text{lap}}(t) = T_{\text{base}} - \Delta T_{\text{fuel}} \cdot (M_{\text{initial}} - M_{\text{fuel}}(t)) - \Delta T_{\text{track}}(t) + D(t) + \epsilon$$

Where:
- $T_{\text{base}}$: Driver's baseline pace on fresh tyres with zero fuel load.
- $\Delta T_{\text{fuel}}$: Fuel mass sensitivity (~0.03 seconds per kg burned).
- $\Delta T_{\text{track}}(t)$: Track grip evolution / rubbering-in factor over time.
- $D(t)$: True tyre degradation lap time penalty.
- $\epsilon \sim \mathcal{N}(0, \sigma^2)$: Random traffic / driver noise.

### Weighted Least Squares (WLS) Wear Curve
Tyre degradation $D(t)$ as a function of stint age $a$ is modeled via a non-linear two-phase equation:

$$D(a) = \alpha \cdot a + \beta \cdot \max(0, a - a_{\text{cliff}})^2$$

- Linear Phase ($\alpha \cdot a$): Thermal and mechanical wear penalty (typically 0.04s to 0.12s per lap).
- Non-Linear Phase ($\beta \cdot (a - a_{\text{cliff}})^2$): Exponential pace drop after hitting cliff age $a_{\text{cliff}}$.

### Bayesian Posterior Cliff Lap Prediction
To predict the exact lap when the tyre cliff will occur before it happens, TrackShift maintains a Bayesian posterior distribution over candidate cliff laps $L_{\text{cliff}} \in [10, 45]$:

$$P(L_{\text{cliff}} = k \mid \mathcal{D}_{1..t}) = \frac{P(\mathcal{D}_{1..t} \mid L_{\text{cliff}} = k) \cdot P(L_{\text{cliff}} = k)}{\sum_{j} P(\mathcal{D}_{1..t} \mid L_{\text{cliff}} = j) \cdot P(L_{\text{cliff}} = j)}$$

When $P(L_{\text{cliff}} \le t + 2 \mid \mathcal{D}) > 0.70$, the engine fires the `TYRE_CLIFF_IMMINENT` event.

---

## ⏱️ 2. Compound Pace Intelligence

Pace intelligence computes the degradation-free pace $P_c(t)$ for each compound $c \in \{\text{SOFT}, \text{MEDIUM}, \text{HARD}\}$:

$$\text{Pace}_{\text{SOFT}} = \text{BasePace} - 0.65\text{s}$$
$$\text{Pace}_{\text{MEDIUM}} = \text{BasePace}$$
$$\text{Pace}_{\text{HARD}} = \text{BasePace} + 0.55\text{s}$$

Linear trend slopes $S = \frac{d(\text{Pace})}{dt}$ are tracked over rolling 5-lap windows to detect sudden performance drops.

---

## 🎯 3. Multi-Objective Strategy Decision Engine

The [`StrategyEngine`](file:///e:/f1/backend/strategy/engine.py) evaluates candidate actions $A \in \{\text{STAY\_OUT}, \text{PIT\_SOFT}, \text{PIT\_MEDIUM}, \text{PIT\_HARD}, \text{UNDERCUT}, \text{OVERCUT}\}$ at each decision tick.

### Multi-Objective Objective Function

$$\min_{A} J(A) = T_{\text{remaining}}(A) + w_{\text{traffic}} \cdot R_{\text{traffic}}(A) + w_{\text{weather}} \cdot R_{\text{weather}}(A) + P_{\text{invalidation}}(A)$$

Where:
- $T_{\text{remaining}}(A)$: Total projected race time from current lap to chequered flag under action $A$.
- $R_{\text{traffic}}(A)$: Expected time lost stuck in dirty air / behind slower cars upon pit re-entry.
- $R_{\text{weather}}(A)$: Risk multiplier if compound choice conflicts with incoming rain.
- $P_{\text{invalidation}}(A)$: Penalty added if action violates mandatory 2-compound rules or unsafe release windows.

### Pit Loss Dynamics

Pit stop time penalty $L_{\text{pit}}$ varies dynamically based on active track flag conditions:

$$L_{\text{pit}} = \begin{cases} 
22.0\text{s} & \text{under GREEN flag} \\
14.0\text{s} & \text{under VSC (Virtual Safety Car)} \\
11.0\text{s} & \text{under full SAFETY CAR} 
\end{cases}$$

---

## 🔮 4. Monte Carlo Position Predictor

The [`MonteCarloPositionPredictor`](file:///e:/f1/models/position_model/) executes 1,000 forward race stochastic simulations to project the probability distribution of finishing positions $P(\text{Finish} = k)$.

```
For sim = 1 to 1000:
   1. Sample driver pace from N(μ_pace, σ_pace)
   2. Sample tyre wear progression from WLS posterior
   3. Sample SC/VSC occurrence probability per lap (~3% base)
   4. Simulate forward lap times & pit stops for all 20 cars
   5. Record finishing positions
Result: Finishing position expectation E[Pos] and variance Var(Pos)
```

### Strategic Action Confidence Scoring

$$\text{Confidence}(A) = 1.0 - \min\left(1.0, \frac{\sigma_{T}(A)}{3.0}\right) \cdot \left(1.0 - \frac{\text{Margin}(A)}{5.0}\right)$$

Where $\text{Margin}(A)$ is the time delta between the top recommendation and the second-best alternative.
