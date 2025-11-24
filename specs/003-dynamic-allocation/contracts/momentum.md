# Contract: Momentum Strategy Weight Calculation

**Strategy**: Momentum-Based Dynamic Allocation
**Purpose**: Specify exact calculation rules and accuracy requirements for momentum weight calculations

## Calculation Contract

### Input Specification

**Required Inputs**:
- `calculation_date`: Date for which weights are calculated (type: `datetime.date`)
- `price_data`: Historical price DataFrame with columns `[date, symbol, price]` (type: `pd.DataFrame`)
- `parameters`: `MomentumParameters` object containing:
  - `lookback_days`: Integer, 1 ≤ value ≤ 500
  - `assets`: List of asset symbols (non-empty, unique)
  - `exclude_negative`: Boolean (default `True`)
  - `min_momentum`: Optional Decimal threshold

**Data Requirements**:
- Price data must include at least `lookback_days` trading days before `calculation_date`
- Prices must be non-negative
- Each asset must have continuous price history (no gaps) within lookback window

### Calculation Steps

**Step 1: Extract Price Window**
```python
# Get prices for lookback period, ending BEFORE calculation_date
window_end_date = calculation_date - timedelta(days=1)
window_start_date = calculation_date - timedelta(days=lookback_days + buffer)

# Filter to lookback window
price_window = get_last_n_trading_days(price_data, calculation_date, lookback_days)
```

**Expected Result**: DataFrame with exactly `lookback_days` rows per asset

---

**Step 2: Calculate Momentum Scores**
```python
for each asset in parameters.assets:
    price_start = price_window[asset].iloc[0]   # First price in window
    price_end = price_window[asset].iloc[-1]    # Last price in window

    momentum_score[asset] = (price_end / price_start) - 1.0
```

**Formula**:
```
Momentum = (P_end / P_start) - 1.0
```

Where:
- `P_start` = Price at beginning of lookback period (oldest date in window)
- `P_end` = Price at end of lookback period (most recent date before calculation_date)

**Expected Output**: Dictionary of `{symbol: float}` representing cumulative returns

**Accuracy Requirement**: Momentum scores must be accurate to 6 decimal places (0.000001)

---

**Step 3: Apply Filters**
```python
if parameters.exclude_negative:
    filtered_scores = {k: max(0, v) for k, v in momentum_scores.items()}
else:
    filtered_scores = momentum_scores

if parameters.min_momentum is not None:
    filtered_scores = {k: v for k, v in filtered_scores.items() if v >= parameters.min_momentum}
```

**Filter Rules**:
1. If `exclude_negative=True`: Zero out any negative momentum scores
2. If `min_momentum` is set: Remove assets with momentum below threshold

**Edge Case**: If all scores filtered out → allocate 100% to cash

---

**Step 4: Normalize Weights**
```python
total_score = sum(filtered_scores.values())

if total_score == 0:
    # All assets have zero/negative momentum
    weights = {parameters.cash_symbol: Decimal("1.0")}
else:
    # Proportional allocation
    weights = {
        symbol: Decimal(str(score / total_score)).quantize(Decimal("0.0001"))
        for symbol, score in filtered_scores.items()
    }

# Ensure exact sum = 1.0
weight_sum = sum(weights.values())
if weight_sum != Decimal("1.0"):
    largest_asset = max(weights.keys(), key=lambda k: weights[k])
    weights[largest_asset] += (Decimal("1.0") - weight_sum)
```

**Normalization Rules**:
1. Sum of all raw scores → denominator
2. Each weight = (asset_score / total_score)
3. Round to 4 decimal places
4. Adjust largest weight to ensure sum = exactly 1.0

**Accuracy Requirement**: Final weights sum must equal 1.0 within tolerance of 0.0001

---

### Output Specification

**Return Type**: `CalculatedWeights` object

**Required Fields**:
- `calculation_date`: Same as input
- `weights`: Dict[str, Decimal] with sum = 1.0 ± 0.0001
- `strategy_name`: Strategy identifier
- `parameters_snapshot`: JSON-serializable dict of parameters used
- `excluded_assets`: List of assets excluded due to negative momentum or threshold
- `metadata`: Dict containing `momentum_scores` for audit trail

**Example Output**:
```python
CalculatedWeights(
    calculation_date=date(2020, 6, 15),
    weights={
        "SPY": Decimal("0.7500"),
        "AGG": Decimal("0.2500")
    },
    strategy_name="momentum_120d",
    parameters_snapshot={
        "lookback_days": 120,
        "assets": ["SPY", "AGG", "GLD"],
        "exclude_negative": True
    },
    excluded_assets=["GLD"],  # Had negative momentum
    used_previous_weights=False,
    metadata={
        "momentum_scores": {
            "SPY": 0.15,
            "AGG": 0.05,
            "GLD": -0.03
        }
    }
)
```

---

## Test Cases

### Test Case 1: Basic Positive Momentum

**Inputs**:
```python
calculation_date = date(2020, 6, 15)
lookback_days = 5
assets = ["SPY", "AGG"]

price_data = {
    "date": [
        date(2020, 6, 8), date(2020, 6, 8),   # Day 1
        date(2020, 6, 9), date(2020, 6, 9),   # Day 2
        date(2020, 6, 10), date(2020, 6, 10), # Day 3
        date(2020, 6, 11), date(2020, 6, 11), # Day 4
        date(2020, 6, 12), date(2020, 6, 12), # Day 5
    ],
    "symbol": ["SPY", "AGG"] * 5,
    "price": [
        100.0, 110.0,  # Day 1: SPY=100, AGG=110
        102.0, 111.0,  # Day 2
        105.0, 112.0,  # Day 3
        108.0, 112.5,  # Day 4
        110.0, 113.0,  # Day 5: SPY=110, AGG=113
    ]
}
```

**Expected Momentum Scores**:
```python
SPY: (110.0 / 100.0) - 1.0 = 0.10 (10% return)
AGG: (113.0 / 110.0) - 1.0 = 0.027273 (2.73% return)
```

**Expected Weights** (exclude_negative=True):
```python
total_score = 0.10 + 0.027273 = 0.127273
SPY: 0.10 / 0.127273 = 0.7857 → Decimal("0.7857")
AGG: 0.027273 / 0.127273 = 0.2143 → Decimal("0.2143")
```

**Validation**:
- Sum: 0.7857 + 0.2143 = 1.0000 ✓
- All weights non-negative ✓
- All weights ≤ 1.0 ✓

---

### Test Case 2: All Negative Momentum

**Inputs**:
```python
calculation_date = date(2020, 6, 15)
lookback_days = 3
assets = ["SPY", "AGG"]

price_data = {
    "date": [
        date(2020, 6, 10), date(2020, 6, 10),
        date(2020, 6, 11), date(2020, 6, 11),
        date(2020, 6, 12), date(2020, 6, 12),
    ],
    "symbol": ["SPY", "AGG"] * 3,
    "price": [
        110.0, 115.0,  # Day 1
        105.0, 113.0,  # Day 2
        100.0, 110.0,  # Day 3: Both declined
    ]
}
```

**Expected Momentum Scores**:
```python
SPY: (100.0 / 110.0) - 1.0 = -0.0909 (negative)
AGG: (110.0 / 115.0) - 1.0 = -0.0435 (negative)
```

**Expected Weights** (exclude_negative=True):
```python
All scores negative → Allocate to cash
weights = {"CASH": Decimal("1.0")}
excluded_assets = ["SPY", "AGG"]
```

**Validation**:
- Cash allocation = 1.0 ✓
- All risky assets excluded ✓

---

### Test Case 3: Mixed Momentum

**Inputs**:
```python
calculation_date = date(2020, 6, 15)
lookback_days = 3
assets = ["SPY", "AGG", "GLD"]

price_data = {
    "date": [date(2020, 6, 10)] * 3 + [date(2020, 6, 11)] * 3 + [date(2020, 6, 12)] * 3,
    "symbol": ["SPY", "AGG", "GLD"] * 3,
    "price": [
        100.0, 110.0, 150.0,  # Day 1
        105.0, 112.0, 148.0,  # Day 2
        110.0, 111.0, 145.0,  # Day 3
    ]
}
```

**Expected Momentum Scores**:
```python
SPY: (110.0 / 100.0) - 1.0 = 0.10
AGG: (111.0 / 110.0) - 1.0 = 0.0091
GLD: (145.0 / 150.0) - 1.0 = -0.0333 (negative)
```

**Expected Weights** (exclude_negative=True):
```python
Filtered: SPY=0.10, AGG=0.0091, GLD=0 (excluded)
total_score = 0.10 + 0.0091 = 0.1091
SPY: 0.10 / 0.1091 = 0.9166 → Decimal("0.9166")
AGG: 0.0091 / 0.1091 = 0.0834 → Decimal("0.0834")
```

**Validation**:
- Sum: 0.9166 + 0.0834 = 1.0000 ✓
- GLD excluded from weights ✓
- excluded_assets = ["GLD"] ✓

---

### Test Case 4: Insufficient Data

**Inputs**:
```python
calculation_date = date(2020, 6, 15)
lookback_days = 120
assets = ["SPY"]

price_data: Only 90 days of data available
```

**Expected Behavior**:
```python
Raise InsufficientDataError:
    "Cannot calculate momentum: only 90 days available, need 120"
```

**Caller Handling**:
- If previous weights exist: Use them (set `used_previous_weights=True`)
- If no previous weights: Propagate error (cannot initialize strategy)

---

### Test Case 5: Min Momentum Threshold

**Inputs**:
```python
calculation_date = date(2020, 6, 15)
lookback_days = 5
assets = ["SPY", "AGG", "GLD"]
min_momentum = Decimal("0.05")  # 5% minimum

Momentum scores:
  SPY: 0.10 (above threshold)
  AGG: 0.02 (below threshold)
  GLD: 0.08 (above threshold)
```

**Expected Weights**:
```python
Filtered: SPY=0.10, GLD=0.08 (AGG excluded)
total_score = 0.18
SPY: 0.10 / 0.18 = 0.5556 → Decimal("0.5556")
GLD: 0.08 / 0.18 = 0.4444 → Decimal("0.4444")
excluded_assets = ["AGG"]
```

---

## Accuracy Requirements

### Numerical Precision

**Momentum Score Calculation**:
- Intermediate division: Use float64 (Python native)
- Accuracy: 6 decimal places (0.000001)
- Formula: `(price_end / price_start) - 1.0`

**Weight Calculation**:
- Intermediate division: float64
- Final weights: Decimal with 4 decimal places
- Conversion: `Decimal(str(float_value)).quantize(Decimal("0.0001"))`

**Weight Sum Validation**:
- Tolerance: 0.0001 (1 basis point)
- Enforcement: Adjust largest weight if sum ≠ 1.0

### Edge Case Handling

**Division by Zero**:
- `price_start = 0`: Raise `ValidationError("Invalid price data: price cannot be zero")`
- `total_score = 0`: Allocate 100% to cash (handled by normalization logic)

**Floating Point Precision**:
- Momentum calculations acceptable in float64
- Convert to Decimal only for final weight storage
- Use `Decimal(str(value))` to avoid precision loss

---

## Validation Rules

### Pre-Calculation Validation

1. `calculation_date` must be a valid date
2. `price_data` must have required columns: [date, symbol, price]
3. `lookback_days` ≥ 1
4. `assets` list must be non-empty
5. All `assets` must exist in `price_data`

### Post-Calculation Validation

1. Weights sum = 1.0 ± 0.0001
2. All weights ≥ 0 (non-negative)
3. All weights ≤ 1.0
4. Weight keys ⊆ (assets ∪ {cash_symbol})
5. If `used_previous_weights=True`, current weights = previous weights

---

## Error Handling

**InsufficientDataError**:
- Condition: `available_days < lookback_days`
- Message: Include actual vs required days
- Caller responsibility: Use previous weights or delay start

**MissingDataError**:
- Condition: Asset has NaN/null prices within window
- Action: Exclude asset from calculation
- Record in `excluded_assets` field

**ValidationError**:
- Condition: Post-calculation checks fail (e.g., weights don't sum to 1.0)
- Action: Raise error with diagnostic info
- Should not occur if implementation correct

---

## Implementation Checklist

- [ ] Extract price window for lookback period
- [ ] Calculate momentum scores using (P_end / P_start) - 1.0
- [ ] Apply negative momentum filter if enabled
- [ ] Apply minimum momentum threshold if set
- [ ] Handle all-negative case (allocate to cash)
- [ ] Normalize weights to sum to 1.0
- [ ] Convert to Decimal with 4 decimal places
- [ ] Adjust largest weight for exact sum
- [ ] Populate CalculatedWeights object
- [ ] Validate all post-conditions
- [ ] Write unit tests for each test case above
- [ ] Write contract test verifying numerical accuracy

---

**Contract Status**: Complete
**Ready for**: Implementation and test-first development
