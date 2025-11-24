# Data Model: Dynamic Asset Allocation

**Feature**: 003-dynamic-allocation
**Date**: 2025-11-24
**Purpose**: Define data entities, relationships, validation rules, and state transitions for dynamic allocation strategies

## Overview

This document specifies the data model for dynamic asset allocation strategies. The model extends the existing `AllocationStrategy` framework with dynamic weight calculation capabilities while maintaining backward compatibility.

---

## Entity Specifications

### 1. DynamicAllocationStrategy (Base Class)

**Purpose**: Abstract base for all dynamic allocation strategies that calculate weights based on historical data.

**Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `name` | `str` | Yes | N/A | Length > 0 | Strategy display name |
| `strategy_type` | `str` | Yes | N/A | Enum: "momentum", "risk_parity", "dual_ma" | Strategy algorithm type |
| `parameters` | `StrategyParameters` | Yes | N/A | Type-specific validation | Algorithm configuration |
| `include_cash` | `bool` | No | `True` | N/A | Whether to support cash allocation |
| `cash_symbol` | `str` | No | `"CASH"` | Length > 0 | Symbol representing cash asset |

**Methods**:

```python
def calculate_weights(
    self,
    calculation_date: date,
    price_data: pd.DataFrame
) -> CalculatedWeights:
    """
    Calculate asset weights for given date using historical data.

    Args:
        calculation_date: Date for weight calculation (weights apply after this date)
        price_data: Historical price DataFrame with columns [date, symbol, price]

    Returns:
        CalculatedWeights object with asset allocations and metadata

    Raises:
        InsufficientDataError: Not enough historical data for lookback period
        MissingDataError: Required asset has missing data points in window
        ValidationError: Invalid calculation results (e.g., weights don't sum to 1.0)
    """
    pass  # Abstract method, implemented by concrete strategies

def validate_parameters(self) -> None:
    """
    Validate strategy parameters for correctness.

    Raises:
        ValueError: If parameters are invalid
    """
    pass  # Implemented by base class using parameters.validate()
```

**Relationships**:
- **Extends**: `AllocationStrategy` (for backward compatibility)
- **Composes**: `StrategyParameters` (1:1 relationship)
- **Produces**: `CalculatedWeights` (1:N, one per calculation date)

**Validation Rules**:
- `name` must not be empty
- `strategy_type` must match implemented strategy types
- `parameters` must pass type-specific validation
- If `include_cash=True`, `cash_symbol` must be defined

---

### 2. StrategyParameters (Base Class)

**Purpose**: Base configuration for all dynamic strategies.

**Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `lookback_days` | `int` | Yes | N/A | 1 ≤ value ≤ 500 | Historical data window size |
| `assets` | `list[str]` | Yes | N/A | Length ≥ 1, no duplicates | Asset symbols to allocate |

**Methods**:

```python
def validate(self) -> None:
    """
    Validate common parameters.

    Raises:
        ValueError: If validation fails
    """
    # Implemented in base class

def get_required_history_days(self) -> int:
    """
    Calculate minimum historical data required.

    Returns:
        Number of days needed before first calculation
    """
    return self.lookback_days  # Override in subclasses if more needed
```

**Subclasses**: `MomentumParameters`, `RiskParityParameters`, `DualMomentumParameters`

**Validation Rules**:
- `lookback_days` must be positive integer
- `lookback_days` ≥ 30 (warn if less, may be noisy)
- `lookback_days` ≤ 500 (reject if more, likely error)
- `assets` list must not be empty
- `assets` must contain unique symbols (no duplicates)

---

### 3. MomentumParameters

**Purpose**: Configuration for momentum-based strategy.

**Extends**: `StrategyParameters`

**Additional Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `exclude_negative` | `bool` | No | `True` | N/A | Zero out assets with negative momentum |
| `min_momentum` | `Decimal | None` | No | `None` | If set, value ≥ 0 | Minimum momentum to include asset |

**Example**:
```python
MomentumParameters(
    lookback_days=120,
    assets=["SPY", "AGG", "GLD"],
    exclude_negative=True,
    min_momentum=None
)
```

**Validation Rules**:
- All base class validations apply
- If `min_momentum` is set, must be non-negative Decimal
- `exclude_negative=False` with `min_momentum=0` is equivalent to `exclude_negative=True`

---

### 4. RiskParityParameters

**Purpose**: Configuration for volatility-adjusted (risk parity) strategy.

**Extends**: `StrategyParameters`

**Additional Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `target_volatility` | `Decimal | None` | No | `None` | If set, 0.01 ≤ value ≤ 0.50 | Target portfolio volatility (annualized) |
| `min_volatility_threshold` | `Decimal` | No | `Decimal("0.0001")` | Value > 0 | Minimum volatility to include asset |
| `annualization_factor` | `int` | No | `252` | Value > 0 | Trading days per year for annualizing |

**Example**:
```python
RiskParityParameters(
    lookback_days=120,
    assets=["SPY", "AGG", "GLD"],
    target_volatility=Decimal("0.12"),  # 12% annual volatility target
    min_volatility_threshold=Decimal("0.0001"),
    annualization_factor=252
)
```

**Validation Rules**:
- All base class validations apply
- If `target_volatility` is set:
  - Must be between 1% and 50% (0.01 ≤ value ≤ 0.50)
  - Must be positive Decimal
- `min_volatility_threshold` must be positive (> 0)
- `annualization_factor` typically 252 (daily), 52 (weekly), 12 (monthly)

---

### 5. DualMomentumParameters

**Purpose**: Configuration for dual moving average strategy.

**Extends**: `StrategyParameters`

**Additional Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `short_window` | `int` | Yes | N/A | 1 ≤ value < long_window | Short-term moving average period |
| `long_window` | `int` | Yes | N/A | Value > short_window | Long-term moving average period |
| `use_signal_strength` | `bool` | No | `False` | N/A | Weight by signal strength (vs binary) |

**Example**:
```python
DualMomentumParameters(
    lookback_days=200,  # Must be ≥ long_window
    assets=["SPY", "AGG", "GLD"],
    short_window=50,
    long_window=200,
    use_signal_strength=False
)
```

**Validation Rules**:
- All base class validations apply
- `short_window` must be positive integer
- `long_window` must be positive integer
- `short_window` < `long_window` (strict inequality)
- `lookback_days` ≥ `long_window` (need enough data for long MA)
- Common pairs: (10, 30), (20, 60), (50, 200)

**Override**:
```python
def get_required_history_days(self) -> int:
    return self.long_window  # Need at least long window days
```

---

### 6. CalculatedWeights

**Purpose**: Result of dynamic weight calculation with metadata for auditability.

**Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `calculation_date` | `date` | Yes | N/A | Valid date | Date weights were calculated for |
| `weights` | `dict[str, Decimal]` | Yes | N/A | Sum = 1.0 ± 0.0001 | Asset symbol → allocation weight |
| `strategy_name` | `str` | Yes | N/A | Length > 0 | Strategy that produced weights |
| `parameters_snapshot` | `dict` | Yes | N/A | Valid JSON | Parameters used for calculation |
| `excluded_assets` | `list[str]` | No | `[]` | N/A | Assets excluded due to data issues |
| `used_previous_weights` | `bool` | No | `False` | N/A | True if insufficient data, used prior weights |
| `metadata` | `dict` | No | `{}` | Valid JSON | Strategy-specific calculation metadata |

**Methods**:

```python
def validate(self) -> None:
    """
    Validate calculated weights meet requirements.

    Raises:
        ValidationError: If weights invalid
    """
    # Check sum = 1.0 within tolerance
    # Check all weights non-negative
    # Check weight keys match expected assets

def to_dict(self) -> dict:
    """Export to JSON-serializable dict for logging/debugging."""
    pass

def get_asset_weight(self, symbol: str) -> Decimal:
    """Get weight for specific asset, return 0 if not present."""
    return self.weights.get(symbol, Decimal("0"))
```

**Validation Rules**:
- `weights` must sum to 1.0 within tolerance (0.0001)
- All weights must be non-negative (≥ 0)
- All weights must be ≤ 1.0
- `weights` keys should be subset of original assets + cash symbol
- `calculation_date` must be valid date
- `parameters_snapshot` must be serializable to JSON

**Example**:
```python
CalculatedWeights(
    calculation_date=date(2020, 6, 15),
    weights={
        "SPY": Decimal("0.6000"),
        "AGG": Decimal("0.3000"),
        "GLD": Decimal("0.1000")
    },
    strategy_name="momentum_120d",
    parameters_snapshot={
        "lookback_days": 120,
        "assets": ["SPY", "AGG", "GLD"],
        "exclude_negative": True
    },
    excluded_assets=[],
    used_previous_weights=False,
    metadata={
        "momentum_scores": {
            "SPY": 0.15,
            "AGG": 0.05,
            "GLD": 0.02
        }
    }
)
```

---

### 7. PriceWindow

**Purpose**: Extracted historical price data for strategy calculations.

**Attributes**:

| Attribute | Type | Required | Default | Validation | Description |
|-----------|------|----------|---------|------------|-------------|
| `start_date` | `date` | Yes | N/A | Valid date | First date in window |
| `end_date` | `date` | Yes | N/A | end_date > start_date | Last date in window (inclusive) |
| `prices` | `pd.DataFrame` | Yes | N/A | Valid pivot table | Prices indexed by date, columns = symbols |
| `num_days` | `int` | Yes | N/A | Value > 0 | Actual number of trading days in window |

**Methods**:

```python
def get_asset_prices(self, symbol: str) -> pd.Series:
    """Get price series for specific asset."""
    return self.prices[symbol]

def has_complete_data(self, symbol: str) -> bool:
    """Check if asset has all non-null prices in window."""
    return self.prices[symbol].notna().all()

def get_complete_assets(self) -> list[str]:
    """Return list of assets with complete (no missing) data."""
    return [col for col in self.prices.columns if self.has_complete_data(col)]

def validate(self) -> None:
    """
    Validate window data structure.

    Raises:
        ValidationError: If window invalid
    """
    # Check DataFrame not empty
    # Check end_date > start_date
    # Check num_days matches DataFrame length
```

**Validation Rules**:
- `prices` DataFrame must not be empty
- `prices` must be indexed by date
- `prices` columns must be asset symbols
- `start_date` < `end_date`
- `num_days` must equal `len(prices)`
- All prices must be non-negative (≥ 0)

---

## Entity Relationships

```
AllocationStrategy (existing)
    ↑ extends
DynamicAllocationStrategy (new base)
    ↑ implements
    ├── MomentumStrategy
    ├── RiskParityStrategy
    └── DualMomentumStrategy

StrategyParameters (new base)
    ↑ extends
    ├── MomentumParameters
    ├── RiskParityParameters
    └── DualMomentumParameters

DynamicAllocationStrategy → StrategyParameters (composition, 1:1)
DynamicAllocationStrategy → CalculatedWeights (produces, 1:N)
CalculatedWeights → PriceWindow (uses during calculation, transient)

BacktestEngine (existing) → DynamicAllocationStrategy (uses polymorphically)
```

**Polymorphism**:
- `BacktestEngine` accepts `AllocationStrategy` (base type)
- Dynamically checks for `calculate_weights()` method (duck typing)
- Calls `strategy.asset_weights` for static strategies
- Calls `strategy.calculate_weights(date, data)` for dynamic strategies

---

## State Transitions

### Weight Calculation Lifecycle

```
[Start] → Extract Price Window
    ↓
Check Data Sufficiency
    ├─ Sufficient → Calculate Raw Weights → Normalize → [CalculatedWeights]
    │
    └─ Insufficient → Check Previous Weights
        ├─ Available → [Use Previous CalculatedWeights]
        └─ None → [Raise InsufficientDataError]

Edge Cases:
- Missing Data Points → Exclude Asset → Recalculate with Remaining
- All Negative Returns → Allocate to Cash → [CalculatedWeights with 100% cash]
- Zero Volatility → Exclude Asset → Recalculate with Remaining
```

### Strategy Parameter Lifecycle

```
[Create Parameters] → Validate → [Valid Parameters]
    ↓
Pass to Strategy Constructor → Strategy.validate_parameters()
    ↓
[Strategy Ready] → Used for Calculations → [CalculatedWeights Stream]
```

---

## Validation Summary

### Critical Validations (Must Pass)

1. **Parameter Validation** (at strategy creation):
   - Lookback period in valid range (1-500 days)
   - Assets list non-empty, no duplicates
   - Type-specific constraints (e.g., short < long window)

2. **Weight Validation** (after calculation):
   - Sum = 1.0 within tolerance (0.0001)
   - All weights non-negative (≥ 0)
   - All weights ≤ 1.0

3. **Data Validation** (before calculation):
   - Sufficient historical data (≥ lookback_days)
   - Price data valid (non-negative, proper structure)

### Warnings (Should Review)

1. **Parameter Warnings**:
   - Lookback < 30 days (may be noisy)
   - Lookback > 252 days (may be too slow)
   - Short window < 10 days (high turnover)

2. **Calculation Warnings**:
   - Many assets excluded due to missing data (> 50%)
   - Extreme weight concentration (one asset > 80%)
   - Used previous weights repeatedly (> 5 consecutive dates)

---

## Data Precision & Accuracy

### Decimal Type Usage

**Required for**:
- Final calculated weights (4 decimal places)
- Weight sums and normalization
- Strategy parameters involving ratios/percentages

**Not Required for** (float64 acceptable):
- Intermediate pandas calculations (returns, volatility, moving averages)
- Price data storage
- Performance metrics

**Conversion Pattern**:
```python
# Pandas calculations in float
momentum_scores = (prices.iloc[-1] / prices.iloc[0]) - 1.0  # float64

# Convert to Decimal for weight storage
weights = {
    symbol: Decimal(str(score / total)).quantize(Decimal("0.0001"))
    for symbol, score in momentum_scores.items()
}
```

### Rounding Rules

- **Weights**: 4 decimal places (0.0001 precision)
- **Returns**: No rounding during calculation, round only for display
- **Volatility**: No rounding during calculation, round only for display
- **Prices**: 4 decimal places (inherited from existing data loader)

---

## Extensibility

### Adding New Strategy Types

**Steps**:
1. Create new `*Parameters` class extending `StrategyParameters`
2. Implement parameter-specific validation
3. Create new strategy class extending `DynamicAllocationStrategy`
4. Implement `calculate_weights()` method
5. Add unit tests for calculation logic
6. Add contract tests for numerical accuracy
7. Add integration test with `BacktestEngine`

**Example Template**:
```python
@dataclass
class NewStrategyParameters(StrategyParameters):
    """Parameters for new strategy."""
    custom_param: float

    def validate(self) -> None:
        super().validate()
        if self.custom_param <= 0:
            raise ValueError("custom_param must be positive")

class NewStrategy(DynamicAllocationStrategy):
    """New allocation strategy implementation."""

    def __init__(self, name: str, parameters: NewStrategyParameters):
        self.name = name
        self.strategy_type = "new_strategy"
        self.parameters = parameters
        self.validate_parameters()

    def calculate_weights(
        self,
        calculation_date: date,
        price_data: pd.DataFrame
    ) -> CalculatedWeights:
        # Implementation here
        pass
```

---

## Migration from Static Strategies

**Backward Compatibility**:
- Existing `AllocationStrategy` unchanged
- `BacktestEngine` detects strategy type via duck typing
- No breaking changes to existing code

**Conversion Pattern** (if user wants to convert static → dynamic):
```python
# Old static strategy
static_strategy = AllocationStrategy(
    name="60/40 Portfolio",
    asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")}
)

# Cannot directly convert (static weights are fixed)
# User must choose appropriate dynamic strategy and parameters
# Example: momentum strategy targeting similar allocation
dynamic_strategy = MomentumStrategy(
    name="Dynamic 60/40",
    parameters=MomentumParameters(
        lookback_days=120,
        assets=["SPY", "AGG"]
    )
)
```

---

**Data Model Complete**: All entities specified with attributes, relationships, validation rules, and state transitions. Ready for contract specifications and quickstart guide.
