# Research: Dynamic Asset Allocation Strategies

**Feature**: 003-dynamic-allocation
**Date**: 2025-11-24
**Purpose**: Document algorithm research, implementation approaches, and best practices for dynamic allocation strategies

## Overview

This document consolidates research findings for implementing three dynamic asset allocation strategies: momentum-based, risk parity (volatility-adjusted), and dual moving average. Each section includes the algorithm specification, calculation methodology, academic references, and implementation considerations.

## 1. Momentum-Based Strategy

### Algorithm Specification

**Core Concept**: Allocate capital to assets based on their recent performance (momentum). Assets with higher returns over the lookback period receive higher weights.

**Calculation Method**:

1. **Momentum Score Calculation** (for each asset):
   ```
   momentum_score = (price_end / price_start) - 1.0
   ```
   Where:
   - `price_end` = most recent price in lookback window
   - `price_start` = price at beginning of lookback window (e.g., 120 days ago)

2. **Weight Allocation**:
   - **Case 1: All assets have positive momentum**
     ```
     raw_weight[i] = max(0, momentum_score[i])
     final_weight[i] = raw_weight[i] / sum(raw_weight)
     ```

   - **Case 2: All assets have negative momentum** (from clarification)
     ```
     Allocate 100% to cash (zero allocation to risky assets)
     ```

   - **Case 3: Mixed momentum**
     ```
     raw_weight[i] = max(0, momentum_score[i])  # Zero out negative momentum
     final_weight[i] = raw_weight[i] / sum(raw_weight)
     ```

### Academic Foundation

**Primary Reference**: Jegadeesh, N., & Titman, S. (1993). "Returns to Buying Winners and Selling Losers: Implications for Stock Market Efficiency." *Journal of Finance*, 48(1), 65-91.

**Key Findings**:
- Momentum strategies exhibit statistically significant abnormal returns
- Optimal lookback periods typically range from 3-12 months (60-250 trading days)
- Performance persists for 3-12 months after formation
- Risk: Momentum crashes during market reversals

**Additional References**:
- Asness, C. S., Moskowitz, T. J., & Pedersen, L. H. (2013). "Value and Momentum Everywhere." *Journal of Finance*, 68(3), 929-985.

### Implementation Considerations

**Lookback Period Selection**:
- Common values: 60 days (3 months), 120 days (6 months), 252 days (1 year)
- Shorter periods = more responsive but noisier
- Longer periods = smoother but slower to adapt
- Default recommendation: 120 days (balance responsiveness and stability)

**Edge Cases** (per specification clarifications):
- **Insufficient data**: Skip calculation, use previous weights
- **Missing data points**: Exclude asset from that calculation
- **All negative returns**: Move to 100% cash

**Numerical Precision**:
- Use pandas `pct_change()` or manual division with Decimal conversion
- Round final weights to 4 decimal places
- Validate sum = 1.0 within 0.0001 tolerance

**Performance Optimization**:
- Pre-slice DataFrame to lookback window using date indexing
- Use pandas vectorized operations (avoid Python loops)
- Cache price windows if recomputing for parameter optimization

### Expected Behavior

**Example Scenario**:
```
Assets: SPY, AGG, GLD
Lookback: 120 days
Prices (120 days ago): SPY=$300, AGG=$110, GLD=$150
Current Prices: SPY=$330, AGG=$112, GLD=$145

Momentum Scores:
- SPY: (330/300) - 1 = 0.10 (10% return)
- AGG: (112/110) - 1 = 0.018 (1.8% return)
- GLD: (145/150) - 1 = -0.033 (-3.3% return)

Weights (exclude negative):
- raw: SPY=0.10, AGG=0.018, GLD=0 (zeroed out)
- sum = 0.118
- final: SPY=0.10/0.118≈0.847, AGG=0.018/0.118≈0.153, GLD=0
```

---

## 2. Risk Parity (Volatility-Adjusted) Strategy

### Algorithm Specification

**Core Concept**: Allocate capital inversely proportional to asset volatility. Higher volatility assets receive lower weights to equalize risk contribution.

**Calculation Method**:

1. **Volatility Calculation** (for each asset):
   ```
   daily_returns = prices.pct_change()
   daily_std = daily_returns.std(ddof=1)  # Sample std dev
   annualized_volatility = daily_std * sqrt(252)
   ```

2. **Weight Allocation**:
   ```
   inverse_vol[i] = 1.0 / volatility[i]  # Higher vol → lower weight
   final_weight[i] = inverse_vol[i] / sum(inverse_vol)
   ```

3. **Risk Target Adjustment** (optional):
   ```
   If target_volatility specified:
     leverage = target_volatility / portfolio_volatility
     Apply leverage to all weights (scale up/down)
   ```

### Academic Foundation

**Primary Reference**: Qian, E. (2005). "Risk Parity Portfolios: Efficient Portfolios Through True Diversification." *PanAgora Asset Management*.

**Key Concepts**:
- Traditional market-cap weighting concentrates risk in volatile assets
- Equal risk contribution creates more balanced exposure
- Inverse volatility weighting is simplified risk parity
- Full risk parity requires covariance matrix (out of scope for initial implementation)

**Additional References**:
- Maillard, S., Roncalli, T., & Teïletche, J. (2010). "The Properties of Equally Weighted Risk Contribution Portfolios." *Journal of Portfolio Management*, 36(4), 60-70.

### Implementation Considerations

**Volatility Estimation**:
- Use sample standard deviation (ddof=1, not ddof=0)
- Annualization factor: sqrt(252) for daily data, sqrt(12) for monthly
- Minimum window: 30 days for stable estimates; recommend 60+ days
- Default lookback: 120 days (matches momentum for consistency)

**Edge Cases** (per specification clarifications):
- **Zero or near-zero volatility**: Exclude asset from calculation
- **Threshold for "near-zero"**: volatility < 0.0001 (0.01% annualized)
- **Insufficient data**: Skip calculation, use previous weights
- **Missing data points**: Exclude asset from calculation

**Risk Target (Optional Enhancement)**:
- If not specified, use unlevered inverse volatility weights
- If specified (e.g., 10% target volatility):
  1. Calculate portfolio volatility from current weights
  2. Compute leverage factor = target / actual
  3. Scale all weights by leverage (cash fills to 100%)

**Numerical Precision**:
- Pandas operations naturally use float64
- Convert to Decimal for final weight storage
- Round to 4 decimal places

### Expected Behavior

**Example Scenario**:
```
Assets: SPY, AGG, GLD
Lookback: 120 days

Calculated Volatilities:
- SPY: 20% annualized
- AGG: 5% annualized
- GLD: 15% annualized

Inverse Volatilities:
- SPY: 1/0.20 = 5.0
- AGG: 1/0.05 = 20.0
- GLD: 1/0.15 = 6.67

Weights:
- sum = 31.67
- SPY: 5.0/31.67 ≈ 0.158 (15.8%)
- AGG: 20.0/31.67 ≈ 0.632 (63.2%)
- GLD: 6.67/31.67 ≈ 0.211 (21.1%)

Interpretation: Lower-volatility AGG receives highest allocation
```

---

## 3. Dual Moving Average Strategy

### Algorithm Specification

**Core Concept**: Allocate to assets based on trend signals derived from moving average crossovers. Assets in uptrends (short MA > long MA) receive higher weights.

**Calculation Method**:

1. **Moving Average Calculation** (for each asset):
   ```
   short_ma = prices.rolling(window=short_period).mean()
   long_ma = prices.rolling(window=long_period).mean()
   ```

2. **Trend Signal**:
   ```
   if short_ma > long_ma:
       trend_signal[i] = 1.0  # Positive trend
   else:
       trend_signal[i] = 0.0  # Negative trend
   ```

3. **Signal Strength** (optional enhancement):
   ```
   strength[i] = (short_ma - long_ma) / long_ma  # Percentage difference
   weight[i] = max(0, strength[i])  # Zero out negative
   ```

4. **Weight Allocation**:
   - **Simple approach**: Equal weight to assets with positive trend signal
   - **Signal-weighted approach**: Weight proportional to signal strength

### Academic Foundation

**Primary Reference**: Antonacci, G. (2014). *Dual Momentum Investing: An Innovative Strategy for Higher Returns with Lower Risk*. McGraw-Hill Education.

**Key Concepts**:
- Combines absolute momentum (time-series) with relative momentum (cross-sectional)
- Absolute momentum: Asset's trend relative to its own history (MA crossover)
- Relative momentum: Asset's performance relative to peers (addressed in basic momentum strategy)
- Effective for trend-following across asset classes

**Additional References**:
- Faber, M. T. (2007). "A Quantitative Approach to Tactical Asset Allocation." *Journal of Wealth Management*, 9(4), 69-79.
- Brock, W., Lakonishok, J., & LeBaron, B. (1992). "Simple Technical Trading Rules and the Stochastic Properties of Stock Returns." *Journal of Finance*, 47(5), 1731-1764.

### Implementation Considerations

**Moving Average Periods**:
- Common pairs:
  - 50-day / 200-day (standard Golden Cross / Death Cross)
  - 20-day / 60-day (shorter-term, more responsive)
  - 10-day / 30-day (very short-term, high turnover)
- Default recommendation: 50 / 200 for balance
- Short period must be < long period (validate in parameters)

**Edge Cases**:
- **Insufficient data**: Need at least `long_period` days; skip if unavailable
- **Missing data points**: pandas `rolling().mean()` handles NaN automatically (skips them)
- **All assets in downtrend**: Allocate 100% to cash (consistent with momentum strategy)
- **Initialization period**: First `long_period` days will have NaN for long MA

**Weight Allocation Approaches**:

**Approach A: Binary Signal (simpler, recommended for MVP)**:
```python
signals = (short_ma > long_ma).astype(float)
weights = signals / signals.sum() if signals.sum() > 0 else all_cash
```

**Approach B: Signal Strength (more sophisticated)**:
```python
strength = (short_ma - long_ma) / long_ma
positive_strength = strength.clip(lower=0)
weights = positive_strength / positive_strength.sum() if positive_strength.sum() > 0 else all_cash
```

Decision: Use Approach A for initial implementation (simpler, testable), document Approach B for future enhancement.

### Expected Behavior

**Example Scenario (Binary Signal)**:
```
Assets: SPY, AGG, GLD
Short MA: 50 days, Long MA: 200 days

Current Moving Averages:
- SPY: short_ma=$330, long_ma=$320 → Trend: Positive (1.0)
- AGG: short_ma=$110, long_ma=$112 → Trend: Negative (0.0)
- GLD: short_ma=$148, long_ma=$145 → Trend: Positive (1.0)

Weights:
- sum_signals = 2.0
- SPY: 1.0/2.0 = 0.50 (50%)
- AGG: 0.0/2.0 = 0.00 (0%)
- GLD: 1.0/2.0 = 0.50 (50%)
```

---

## 4. Common Implementation Patterns

### Data Window Extraction

**Requirement**: Extract historical price data for lookback window without look-ahead bias.

**Implementation Pattern**:
```python
def get_price_window(
    prices_df: pd.DataFrame,
    calculation_date: date,
    lookback_days: int,
    assets: list[str]
) -> pd.DataFrame:
    """
    Extract price window ending at calculation_date (exclusive).

    Args:
        prices_df: DataFrame with columns [date, symbol, price]
        calculation_date: Date for which to calculate weights
        lookback_days: Number of trading days to look back
        assets: List of asset symbols to include

    Returns:
        DataFrame with prices for lookback window, pivoted by symbol

    Raises:
        InsufficientDataError: If fewer than lookback_days available
    """
    # Filter to dates before calculation_date
    historical_data = prices_df[prices_df['date'] < calculation_date]

    # Filter to required assets
    asset_data = historical_data[historical_data['symbol'].isin(assets)]

    # Get last N days
    window_data = asset_data.groupby('symbol').tail(lookback_days)

    # Validate sufficient data
    for asset in assets:
        asset_rows = window_data[window_data['symbol'] == asset]
        if len(asset_rows) < lookback_days:
            raise InsufficientDataError(f"{asset}: only {len(asset_rows)} days available")

    # Pivot for calculations
    return window_data.pivot(index='date', columns='symbol', values='price')
```

### Weight Normalization

**Requirement**: Ensure weights sum to exactly 1.0 within tolerance.

**Implementation Pattern**:
```python
def normalize_weights(
    raw_weights: dict[str, float],
    tolerance: Decimal = Decimal("0.0001")
) -> dict[str, Decimal]:
    """
    Normalize raw weights to sum to 1.0.

    Args:
        raw_weights: Dict of asset → raw weight (can be any positive values)
        tolerance: Maximum acceptable deviation from 1.0

    Returns:
        Dict of asset → Decimal weight (sum = 1.0)

    Raises:
        ValueError: If all weights are zero or negative
    """
    total = sum(raw_weights.values())

    if total <= 0:
        raise ValueError("Cannot normalize: all weights are zero or negative")

    normalized = {
        asset: Decimal(str(weight / total)).quantize(Decimal("0.0001"))
        for asset, weight in raw_weights.items()
    }

    # Verify sum within tolerance
    weight_sum = sum(normalized.values())
    if abs(weight_sum - Decimal("1.0")) > tolerance:
        # Adjust largest weight to ensure exact sum
        largest_asset = max(normalized.keys(), key=lambda k: normalized[k])
        adjustment = Decimal("1.0") - weight_sum
        normalized[largest_asset] += adjustment

    return normalized
```

### Missing Data Handling

**Requirement**: Exclude assets with incomplete data from calculation.

**Implementation Pattern**:
```python
def filter_complete_assets(
    window_data: pd.DataFrame,
    required_days: int
) -> list[str]:
    """
    Return list of assets with complete data in window.

    Args:
        window_data: DataFrame with date index, asset columns
        required_days: Minimum number of non-null observations required

    Returns:
        List of asset symbols with complete data
    """
    complete_assets = []

    for symbol in window_data.columns:
        non_null_count = window_data[symbol].notna().sum()
        if non_null_count >= required_days:
            complete_assets.append(symbol)

    return complete_assets
```

---

## 5. Integration with Existing Backtesting Engine

### Current Architecture

**Existing Flow**:
1. User creates `AllocationStrategy` with fixed `asset_weights` dict
2. `BacktestEngine.run_backtest()` accepts strategy + config
3. On initialization: Uses `strategy.asset_weights` to create portfolio
4. On rebalancing dates: Uses `strategy.asset_weights` as target weights

### Required Changes

**New Flow for Dynamic Strategies**:
1. User creates `DynamicAllocationStrategy` (extends `AllocationStrategy`)
2. Strategy has `calculate_weights(date, price_data)` method
3. On initialization:
   - Try to calculate weights for start date
   - If insufficient data, delay start until data available
4. On rebalancing dates:
   - Call `strategy.calculate_weights(date, price_data)`
   - Use returned weights as target allocation
   - Handle edge cases (insufficient data → use previous weights)

**Backward Compatibility**:
- Keep `AllocationStrategy` as-is for static strategies
- Add optional `is_dynamic` flag or use duck-typing (check for `calculate_weights` method)
- Engine detects strategy type and routes accordingly

### Proposed Engine Modification Pattern

```python
class BacktestEngine:
    def _get_target_weights(
        self,
        strategy: AllocationStrategy,
        current_date: date,
        price_data: pd.DataFrame
    ) -> dict[str, Decimal]:
        """Get target weights for rebalancing."""

        # Check if dynamic strategy (has calculate_weights method)
        if hasattr(strategy, 'calculate_weights'):
            try:
                return strategy.calculate_weights(current_date, price_data)
            except InsufficientDataError:
                # Use previous weights if available
                if self._previous_weights:
                    return self._previous_weights
                else:
                    raise  # Cannot initialize without data
        else:
            # Static strategy: return fixed weights
            return strategy.asset_weights
```

---

## 6. Parameter Validation Best Practices

### Required Validations

**Lookback Period**:
- Must be positive integer
- Reasonable range: 30 ≤ lookback_days ≤ 500
- Warn if < 60 (may be too noisy) or > 252 (slow to adapt)

**Moving Average Periods**:
- Both must be positive integers
- Short period < long period
- Reasonable ranges: 10 ≤ short ≤ 100, 30 ≤ long ≤ 300

**Risk Target**:
- Must be positive
- Reasonable range: 0.01 ≤ target ≤ 0.50 (1% to 50% annualized)
- Optional (None = no leverage adjustment)

**Asset List**:
- At least 1 asset (plus cash if needed)
- All assets must exist in price data
- No duplicates

### Validation Implementation Pattern

```python
@dataclass
class StrategyParameters:
    """Base parameters for dynamic strategies."""

    lookback_days: int
    assets: list[str]

    def __post_init__(self):
        """Validate parameters after initialization."""
        if self.lookback_days < 1:
            raise ValueError(f"lookback_days must be positive, got {self.lookback_days}")

        if not self.assets:
            raise ValueError("Must specify at least one asset")

        if len(self.assets) != len(set(self.assets)):
            raise ValueError("Duplicate assets not allowed")

        if self.lookback_days < 30:
            warnings.warn(f"lookback_days={self.lookback_days} may be too short for stable estimates")
```

---

## 7. Testing Strategy

### Unit Tests (Per Strategy)

**Momentum Strategy**:
- Test momentum calculation with known price series
- Test weight normalization
- Test all-negative returns → cash allocation
- Test exclude negative momentum assets
- Test insufficient data handling

**Risk Parity Strategy**:
- Test volatility calculation (compare to manual calculation)
- Test inverse volatility weighting
- Test zero/near-zero volatility exclusion
- Test annualization factor (252 for daily data)

**Dual MA Strategy**:
- Test MA calculation (compare to pandas rolling mean)
- Test trend signal generation
- Test weight allocation (binary and strength-based)
- Test all-downtrend → cash allocation

### Integration Tests

**Dynamic Strategy + BacktestEngine**:
- Run full backtest with dynamic strategy
- Verify weights change over time
- Compare performance to static benchmark
- Test strategy parameter changes produce different results

### Contract Tests (Accuracy)

**Numerical Precision**:
- Verify weights sum to 1.0 within tolerance
- Verify Decimal precision maintained
- Test edge cases (very small/large numbers)

**Calculation Reproducibility**:
- Same inputs → same outputs (deterministic)
- Document random seed if any randomness used (none planned)

---

## 8. Performance Optimization Considerations

### Identified Bottlenecks

1. **Price window extraction**: Filtering large DataFrames repeatedly
2. **Lookback calculations**: Computing on overlapping windows
3. **Parameter optimization**: Running many backtest iterations

### Optimization Strategies

**Level 1: Efficient pandas operations** (implement first):
- Use vectorized operations (avoid Python loops)
- Pre-filter DataFrame to relevant date range
- Use `groupby` and `tail` for window extraction
- Index by date for faster slicing

**Level 2: Caching** (implement if Level 1 insufficient):
- Cache calculated weights by (strategy, date, parameters)
- Cache price windows by (date, lookback_days)
- Use functools.lru_cache for pure functions

**Level 3: Parallel processing** (future enhancement):
- Run parameter combinations in parallel (multiprocessing)
- Only if optimization suite takes > 5 minutes

**Decision**: Start with Level 1, measure performance, escalate only if gates fail.

---

## 9. Open Questions & Future Enhancements

### Resolved Questions

All critical clarifications resolved in `/speckit.clarify` phase:
- ✅ Weight constraints: No min/max per asset
- ✅ Insufficient data: Skip calculation, use previous weights
- ✅ All negative returns: Allocate to cash
- ✅ Missing data points: Exclude asset from calculation
- ✅ Zero volatility: Exclude asset from calculation

### Future Enhancement Opportunities

**Not in Scope for Initial Implementation** (document for future):

1. **Advanced risk parity**: Use covariance matrix instead of simple inverse volatility
2. **Machine learning strategies**: Predictive models (LSTM, Random Forest)
3. **Multi-factor strategies**: Combine momentum + value + quality signals
4. **Transaction cost optimization**: Minimize turnover while maintaining strategy
5. **Adaptive parameters**: Dynamically adjust lookback based on market regime
6. **Walk-forward analysis**: Test parameter stability over time
7. **Signal strength weighting**: Use gradient of signal instead of binary (for dual MA)

---

## 10. Implementation Checklist

**Phase 0 (Research)**: ✅ Complete
- [x] Document momentum algorithm and references
- [x] Document risk parity algorithm and references
- [x] Document dual MA algorithm and references
- [x] Define common implementation patterns
- [x] Specify integration approach with existing engine
- [x] Define parameter validation strategy
- [x] Outline testing strategy
- [x] Identify performance considerations

**Phase 1 (Design)**: Next
- [ ] Create data-model.md with entity specifications
- [ ] Create contracts/ with calculation accuracy specs
- [ ] Create quickstart.md with usage examples
- [ ] Update agent context with new technologies

**Phase 2 (Implementation)**: After Phase 1
- [ ] Generate tasks.md from design artifacts
- [ ] Implement test-first workflow per constitution
- [ ] Verify all gates pass before merge

---

**Research Complete**: All unknowns from Technical Context resolved. Ready to proceed to Phase 1: Design & Contracts.
