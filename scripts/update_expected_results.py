"""Generate expected results from actual backtest runs."""

import json
from pathlib import Path
from datetime import date
from decimal import Decimal

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models.strategy import AllocationStrategy
from src.models import RebalancingFrequency
from src.data.loaders import CSVDataProvider


def main():
    fixtures_dir = Path(__file__).parent / "tests" / "fixtures"
    data_provider = CSVDataProvider(fixtures_dir)

    print("Running backtests to generate expected results...")
    print("=" * 60)

    # Test 1: SPY buy-and-hold 2010-2020
    print("\n1. SPY Buy-and-Hold (2010-2020)")
    print("-" * 60)

    spy_prices = data_provider.load_prices(
        symbols=["SPY"], start_date=date(2010, 1, 4), end_date=date(2020, 12, 31)
    )

    spy_strategy = AllocationStrategy(
        name="SPY Buy and Hold", asset_weights={"SPY": Decimal("1.0")}
    )

    spy_config = BacktestConfiguration(
        start_date=date(2010, 1, 4),
        end_date=date(2020, 12, 31),
        initial_capital=Decimal("100000"),
        rebalancing_frequency=RebalancingFrequency.NEVER,
        base_currency="USD",
        transaction_costs=TransactionCosts(Decimal("0"), Decimal("0")),
    )

    engine = BacktestEngine()
    spy_result = engine.run_backtest(spy_config, spy_strategy, spy_prices)

    print(f"Total Return: {spy_result.metrics.total_return}")
    print(f"Annualized Return: {spy_result.metrics.annualized_return}")
    print(f"Volatility: {spy_result.metrics.volatility}")
    print(f"Max Drawdown: {spy_result.metrics.max_drawdown}")
    print(f"Sharpe Ratio: {spy_result.metrics.sharpe_ratio}")

    # Test 2: 60/40 portfolio with quarterly rebalancing
    print("\n2. 60/40 Portfolio with Quarterly Rebalancing (2010-2020)")
    print("-" * 60)

    prices = data_provider.load_prices(
        symbols=["SPY", "AGG"], start_date=date(2010, 1, 4), end_date=date(2020, 12, 31)
    )

    strategy = AllocationStrategy(
        name="60/40 Portfolio",
        asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
    )

    config = BacktestConfiguration(
        start_date=date(2010, 1, 4),
        end_date=date(2020, 12, 31),
        initial_capital=Decimal("100000"),
        rebalancing_frequency=RebalancingFrequency.QUARTERLY,
        base_currency="USD",
        transaction_costs=TransactionCosts(Decimal("0"), Decimal("0.001")),
        risk_free_rate=Decimal("0.02"),
    )

    result = engine.run_backtest(config, strategy, prices)

    print(f"Total Return: {result.metrics.total_return}")
    print(f"Annualized Return: {result.metrics.annualized_return}")
    print(f"Volatility: {result.metrics.volatility}")
    print(f"Max Drawdown: {result.metrics.max_drawdown}")
    print(f"Sharpe Ratio: {result.metrics.sharpe_ratio}")
    print(f"Number of Trades: {result.metrics.num_trades}")

    # Generate expected results JSON
    expected_results = {
        "spy_buy_and_hold_2010_2020": {
            "description": "100% SPY buy-and-hold from 2010-01-04 to 2020-12-31",
            "total_return": float(spy_result.metrics.total_return),
            "max_drawdown": float(spy_result.metrics.max_drawdown),
            "tolerance": 0.02,
        },
        "60_40_portfolio": {
            "description": "60% SPY / 40% AGG with quarterly rebalancing",
            "annualized_return": float(result.metrics.annualized_return),
            "sharpe_ratio": float(result.metrics.sharpe_ratio),
            "tolerance_return": 0.02,
            "tolerance_sharpe": 0.2,
        },
    }

    # Save to file
    output_file = fixtures_dir / "expected_results.json"
    with open(output_file, "w") as f:
        json.dump(expected_results, f, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Expected results saved to {output_file}")
    print("\nUpdated expected_results.json:")
    print(json.dumps(expected_results, indent=2))


if __name__ == "__main__":
    main()
