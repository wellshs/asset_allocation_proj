"""Example: Backtesting 무한매수법 and 밸류 리밸런싱 strategies.

This example demonstrates how to use the new Infinite Buying Method
and Value Rebalancing strategies with historical data.
"""

from datetime import date
from decimal import Decimal
import pandas as pd

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models import RebalancingFrequency
from src.strategies.infinite_buying import InfiniteBuyingStrategy
from src.strategies.value_rebalancing import ValueRebalancingStrategy
from src.models.strategy_params import (
    InfiniteBuyingParameters,
    ValueRebalancingParameters,
)


def load_sample_data() -> pd.DataFrame:
    """Load sample price data for backtesting.

    In practice, you would load this from CSV using CSVDataProvider.
    This creates sample data for demonstration.
    """
    # Create sample TQQQ price data (3x leveraged Nasdaq ETF)
    # Start earlier to have enough lookback data
    dates = pd.date_range("2019-12-01", "2020-12-31", freq="B")  # Business days

    # Simulate volatile price movement (leveraged ETF)
    import numpy as np

    np.random.seed(42)
    prices = [100.0]
    for _ in range(len(dates) - 1):
        # Random walk with upward bias
        change = np.random.normal(0.002, 0.03)  # 0.2% daily return, 3% volatility
        prices.append(prices[-1] * (1 + change))

    # Create dataframe with both TQQQ and CASH prices
    tqqq_df = pd.DataFrame(
        {
            "date": dates,
            "symbol": "TQQQ",
            "price": prices,
            "currency": "USD",
        }
    )

    # Add CASH with constant price of 1.0
    cash_df = pd.DataFrame(
        {
            "date": dates,
            "symbol": "CASH",
            "price": [1.0] * len(dates),
            "currency": "USD",
        }
    )

    df = pd.concat([tqqq_df, cash_df], ignore_index=True)

    return df


def backtest_infinite_buying():
    """Backtest the Infinite Buying Method (무한매수법)."""
    print("=" * 70)
    print("Backtesting: Infinite Buying Method (무한매수법)")
    print("=" * 70)

    # Load data
    price_data = load_sample_data()
    print(
        f"\nData period: {price_data['date'].min().date()} to {price_data['date'].max().date()}"
    )
    print(f"Starting price: ${price_data['price'].iloc[0]:.2f}")
    print(f"Ending price: ${price_data['price'].iloc[-1]:.2f}")

    # Configure strategy parameters
    params = InfiniteBuyingParameters(
        lookback_days=30,  # Use 30 days of history for calculations
        assets=["TQQQ"],
        divisions=40,  # Divide capital into 40 parts
        take_profit_pct=Decimal("0.10"),  # Take profit at +10%
        phase_threshold=Decimal("0.50"),  # Switch to conservative at 50% progress
        use_rsi=False,  # Don't use RSI filtering
        conservative_buy_only_below_avg=True,  # Phase 2: only buy below average
    )
    params.validate()

    # Create strategy
    strategy = InfiniteBuyingStrategy(params)

    # Configure backtest
    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),  # Start with $10,000
        start_date=date(2020, 2, 1),  # Start after we have enough history
        end_date=date(2020, 12, 31),
        rebalancing_frequency=RebalancingFrequency.WEEKLY,  # Rebalance weekly
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("1.0"),  # $1 per trade
            percentage=Decimal("0.001"),  # 0.1% commission
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0.02"),  # 2% annual risk-free rate
    )

    # Run backtest
    engine = BacktestEngine()
    result = engine.run_backtest(config, strategy, price_data)

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    final_value = result.portfolio_history[-1].total_value
    print(f"\nFinal Portfolio Value: ${float(final_value):,.2f}")
    print(f"Total Return: {float(result.metrics.total_return) * 100:.2f}%")
    print(f"Annualized Return: {float(result.metrics.annualized_return) * 100:.2f}%")
    print(f"Sharpe Ratio: {float(result.metrics.sharpe_ratio):.2f}")
    print(f"Max Drawdown: {float(result.metrics.max_drawdown) * 100:.2f}%")
    print(f"Number of Trades: {len(result.trades)}")

    # Show some sample trades
    print("\nSample Trades (first 10):")
    for trade in result.trades[:10]:
        action = "BUY" if trade.quantity > 0 else "SELL"
        total = abs(trade.quantity) * trade.price
        print(
            f"  {trade.timestamp}: {action} {abs(float(trade.quantity)):.2f} {trade.asset_symbol} "
            f"@ ${float(trade.price):.2f} = ${float(total):.2f}"
        )

    return result


def backtest_value_rebalancing():
    """Backtest the Value Rebalancing strategy (밸류 리밸런싱)."""
    print("\n\n" + "=" * 70)
    print("Backtesting: Value Rebalancing (밸류 리밸런싱)")
    print("=" * 70)

    # Create SPY price data (more stable than TQQQ)
    import numpy as np

    dates = pd.date_range("2019-12-01", "2020-12-31", freq="B")
    np.random.seed(100)  # Different seed for different pattern
    spy_prices = [330.0]  # SPY typical price
    for _ in range(len(dates) - 1):
        # Less volatile than TQQQ
        change = np.random.normal(0.0005, 0.01)  # 0.05% daily return, 1% volatility
        spy_prices.append(spy_prices[-1] * (1 + change))

    # Create dataframe
    spy_df = pd.DataFrame(
        {
            "date": dates,
            "symbol": "SPY",
            "price": spy_prices,
            "currency": "USD",
        }
    )

    cash_df = pd.DataFrame(
        {
            "date": dates,
            "symbol": "CASH",
            "price": [1.0] * len(dates),
            "currency": "USD",
        }
    )

    price_data = pd.concat([spy_df, cash_df], ignore_index=True)

    print(
        f"\nData period: {price_data['date'].min().date()} to {price_data['date'].max().date()}"
    )
    print(f"Starting price: ${price_data['price'].iloc[0]:.2f}")
    print(f"Ending price: ${price_data['price'].iloc[-1]:.2f}")

    # Configure strategy parameters
    params = ValueRebalancingParameters(
        lookback_days=30,
        assets=["SPY"],
        initial_capital=Decimal("10000"),  # $10,000 initial capital
        gradient=Decimal("10"),  # Gradient value for conservative growth
        upper_band_pct=Decimal("0.05"),  # +5% upper band
        lower_band_pct=Decimal("0.05"),  # -5% lower band
        rebalance_frequency=30,  # Check monthly (30 days)
        value_growth_rate=Decimal("0.10"),  # 10% expected annual growth
    )
    params.validate()

    # Create strategy
    strategy = ValueRebalancingStrategy(params)

    # Configure backtest
    config = BacktestConfiguration(
        initial_capital=Decimal("10000"),
        start_date=date(2020, 2, 1),
        end_date=date(2020, 12, 31),
        rebalancing_frequency=RebalancingFrequency.MONTHLY,  # Rebalance monthly
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("1.0"),
            percentage=Decimal("0.001"),
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0.02"),
    )

    # Run backtest
    engine = BacktestEngine()
    result = engine.run_backtest(config, strategy, price_data)

    # Display results
    print("\n" + "=" * 70)
    print("RESULTS")
    print("=" * 70)
    final_value = result.portfolio_history[-1].total_value
    print(f"\nFinal Portfolio Value: ${float(final_value):,.2f}")
    print(f"Total Return: {float(result.metrics.total_return) * 100:.2f}%")
    print(f"Annualized Return: {float(result.metrics.annualized_return) * 100:.2f}%")
    print(f"Sharpe Ratio: {float(result.metrics.sharpe_ratio):.2f}")
    print(f"Max Drawdown: {float(result.metrics.max_drawdown) * 100:.2f}%")
    print(f"Number of Trades: {len(result.trades)}")

    # Show some sample trades
    print("\nSample Trades (first 10):")
    for trade in result.trades[:10]:
        action = "BUY" if trade.quantity > 0 else "SELL"
        total = abs(trade.quantity) * trade.price
        print(
            f"  {trade.timestamp}: {action} {abs(float(trade.quantity)):.2f} {trade.asset_symbol} "
            f"@ ${float(trade.price):.2f} = ${float(total):.2f}"
        )

    return result


def compare_strategies():
    """Compare both strategies side by side."""
    print("\n\n" + "=" * 70)
    print("STRATEGY COMPARISON")
    print("=" * 70)

    # This would run both backtests and compare results
    # For now, just print guidance
    print("\nTo compare strategies:")
    print("1. Run both backtests with the same time period and initial capital")
    print("2. Compare metrics: total return, Sharpe ratio, max drawdown")
    print("3. Analyze trade frequency and transaction costs")
    print("4. Consider risk profile and volatility")

    print("\nInfinite Buying Method is best for:")
    print("  - Leveraged ETFs (TQQQ, SOXL)")
    print("  - High volatility assets")
    print("  - Accumulation phase")

    print("\nValue Rebalancing is best for:")
    print("  - Broad market ETFs (SPY, QQQ)")
    print("  - Long-term growth with bands")
    print("  - Conservative investors")


if __name__ == "__main__":
    # Run examples
    try:
        result1 = backtest_infinite_buying()
        result2 = backtest_value_rebalancing()
        compare_strategies()

        print("\n" + "=" * 70)
        print("Backtest completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"\nError during backtest: {e}")
        raise
