# Contract: Risk Parity Strategy Weight Calculation

**Strategy**: Volatility-Adjusted (Risk Parity) Dynamic Allocation
**Purpose**: Specify exact calculation rules and accuracy requirements for risk parity weight calculations

## Calculation Formula

### Step 1: Calculate Returns
```python
daily_returns = prices.pct_change().dropna()
```

### Step 2: Calculate Volatility (Annualized)
```python
daily_std = daily_returns.std(ddof=1)  # Sample standard deviation
annualized_volatility = daily_std * sqrt(annualization_factor)
# Default annualization_factor = 252 for daily data
```

**Formula**:
```
σ_annual = σ_daily × √252
```

**Accuracy**: Volatility must be accurate to 4 decimal places (0.0001)

### Step 3: Inverse Volatility Weighting
```python
for each asset:
    if volatility[asset] < min_volatility_threshold:
        exclude asset  # Zero or near-zero volatility
    else:
        inverse_vol[asset] = 1.0 / volatility[asset]

weights = normalize(inverse_vol)  # Sum to 1.0
```

**Formula**:
```
w_i = (1/σ_i) / Σ(1/σ_j) for all j not excluded
```

### Step 4: Risk Target Adjustment (Optional)
```python
if target_volatility specified:
    portfolio_vol = calculate_portfolio_volatility(weights, returns)
    leverage = target_volatility / portfolio_vol
    # Apply leverage (scale weights, fill remainder with cash)
```

---

## Test Cases

### Test Case 1: Basic Inverse Volatility
**Input**:
- SPY: 20% annualized volatility
- AGG: 5% annualized volatility
- GLD: 15% annualized volatility

**Expected Weights**:
```
Inverse: SPY=1/0.20=5.0, AGG=1/0.05=20.0, GLD=1/0.15=6.67
Sum = 31.67
Weights: SPY=0.1579, AGG=0.6316, GLD=0.2105
```

### Test Case 2: Zero Volatility Exclusion
**Input**:
- SPY: 20% volatility
- AGG: 0.00005% volatility (below threshold)

**Expected**: AGG excluded, SPY=1.0 (100%)

---

## Accuracy Requirements

- **Volatility calculation**: 4 decimal places
- **Weight calculation**: 4 decimal places
- **Sum validation**: 1.0 ± 0.0001 tolerance
- **Standard deviation**: Use ddof=1 (sample std, not population)

---

**Contract Status**: Complete