# Contract: Dual Moving Average Strategy Weight Calculation

**Strategy**: Dual Moving Average (Trend Following) Dynamic Allocation
**Purpose**: Specify exact calculation rules and accuracy requirements for dual MA weight calculations

## Calculation Formula

### Step 1: Calculate Moving Averages
```python
short_ma = prices.rolling(window=short_window).mean()
long_ma = prices.rolling(window=long_window).mean()
```

### Step 2: Generate Trend Signals
```python
for each asset:
    if short_ma[asset] > long_ma[asset]:
        trend_signal[asset] = 1.0  # Positive trend
    else:
        trend_signal[asset] = 0.0  # Negative/no trend
```

### Step 3: Calculate Weights

**Approach A: Binary Signal (MVP)**:
```python
weights = {
    asset: Decimal(str(signal / sum(signals)))
    for asset, signal in trend_signals.items()
}

if sum(signals) == 0:
    weights = {"CASH": Decimal("1.0")}  # All assets in downtrend
```

**Approach B: Signal Strength (Future Enhancement)**:
```python
strength = (short_ma - long_ma) / long_ma
positive_strength = max(0, strength)
weights = normalize(positive_strength)
```

---

## Test Cases

### Test Case 1: Mixed Trends
**Input**:
- SPY: short_ma=330, long_ma=320 → Signal=1.0 (uptrend)
- AGG: short_ma=110, long_ma=112 → Signal=0.0 (downtrend)
- GLD: short_ma=148, long_ma=145 → Signal=1.0 (uptrend)

**Expected Weights** (Binary):
```
Signals: SPY=1.0, AGG=0.0, GLD=1.0
Sum = 2.0
Weights: SPY=0.50, AGG=0.00, GLD=0.50
```

### Test Case 2: All Downtrends
**Input**: All assets have short_ma < long_ma

**Expected**: 100% allocation to cash

---

## Accuracy Requirements

- **Moving average**: Use pandas `rolling().mean()` (accurate to float64 precision)
- **Trend signal**: Binary (1.0 or 0.0)
- **Weights**: 4 decimal places, sum = 1.0 ± 0.0001

---

**Contract Status**: Complete