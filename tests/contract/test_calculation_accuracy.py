"""Contract tests for calculation accuracy against known scenarios."""

import pytest
import json
from pathlib import Path
from datetime import date
from decimal import Decimal

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models.strategy import AllocationStrategy
from src.models import RebalancingFrequency
from src.data.loaders import CSVDataProvider


# NOTE: These tests require complete historical data (full 10 years of daily prices)
# Historical data has been downloaded using download_historical_data.py


class TestCalculationAccuracy:
    """Test backtesting calculations against known reference scenarios."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to test fixtures directory."""
        return Path(__file__).parent.parent / "fixtures"

    @pytest.fixture
    def expected_results(self, fixtures_dir):
        """Load expected results from JSON."""
        with open(fixtures_dir / "expected_results.json") as f:
            return json.load(f)

    @pytest.fixture
    def data_provider(self, fixtures_dir):
        """Create CSV data provider for test fixtures."""
        return CSVDataProvider(fixtures_dir)

    def test_spy_buy_and_hold_2010_2020(
        self, data_provider, expected_results, fixtures_dir
    ):
        """Test SPY buy-and-hold 2010-2020 against known results.

        This test validates:
        - Total return calculation accuracy
        - Buy-and-hold strategy (no rebalancing)
        - Single asset portfolio
        """
        # Load SPY price data
        prices = data_provider.load_prices(
            symbols=["SPY"], start_date=date(2010, 1, 4), end_date=date(2020, 12, 31)
        )

        # Define 100% SPY strategy
        strategy = AllocationStrategy(
            name="SPY Buy and Hold", asset_weights={"SPY": Decimal("1.0")}
        )

        # Configure backtest (no rebalancing, no costs)
        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.NEVER,
            base_currency="USD",
            transaction_costs=TransactionCosts(Decimal("0"), Decimal("0")),
        )

        # Run backtest
        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        # Validate against expected results
        expected = expected_results["spy_buy_and_hold_2010_2020"]
        tolerance = Decimal(str(expected["tolerance"]))

        total_return = result.metrics.total_return
        expected_return = Decimal(str(expected["total_return"]))

        # Total return should match within tolerance
        assert (
            abs(total_return - expected_return) < tolerance
        ), f"Total return {total_return} doesn't match expected {expected_return}"

        # Max drawdown should be negative and significant
        max_dd = result.metrics.max_drawdown
        expected_dd = Decimal(str(expected["max_drawdown"]))

        assert (
            abs(max_dd - expected_dd) < tolerance
        ), f"Max drawdown {max_dd} doesn't match expected {expected_dd}"

    def test_60_40_portfolio_quarterly_rebalancing(
        self, data_provider, expected_results
    ):
        """Test 60/40 SPY/AGG portfolio with quarterly rebalancing.

        This test validates:
        - Multi-asset portfolio
        - Quarterly rebalancing logic
        - Sharpe ratio calculation
        - Annualized return calculation
        """
        # Load price data for both assets
        prices = data_provider.load_prices(
            symbols=["SPY", "AGG"],
            start_date=date(2010, 1, 4),
            end_date=date(2020, 12, 31),
        )

        # Define 60/40 strategy
        strategy = AllocationStrategy(
            name="60/40 Portfolio",
            asset_weights={"SPY": Decimal("0.6"), "AGG": Decimal("0.4")},
        )

        # Configure backtest with quarterly rebalancing
        config = BacktestConfiguration(
            start_date=date(2010, 1, 4),
            end_date=date(2020, 12, 31),
            initial_capital=Decimal("100000"),
            rebalancing_frequency=RebalancingFrequency.QUARTERLY,
            base_currency="USD",
            transaction_costs=TransactionCosts(Decimal("0"), Decimal("0.001")),
            risk_free_rate=Decimal("0.02"),
        )

        # Run backtest
        engine = BacktestEngine()
        result = engine.run_backtest(config, strategy, prices)

        # Validate results
        expected = expected_results["60_40_portfolio"]

        annualized_return = result.metrics.annualized_return
        expected_return = Decimal(str(expected["annualized_return"]))
        tolerance_return = Decimal(str(expected["tolerance_return"]))

        assert (
            abs(annualized_return - expected_return) < tolerance_return
        ), f"Annualized return {annualized_return} doesn't match expected {expected_return}"

        sharpe_ratio = result.metrics.sharpe_ratio
        expected_sharpe = Decimal(str(expected["sharpe_ratio"]))
        tolerance_sharpe = Decimal(str(expected["tolerance_sharpe"]))

        assert (
            abs(sharpe_ratio - expected_sharpe) < tolerance_sharpe
        ), f"Sharpe ratio {sharpe_ratio} doesn't match expected {expected_sharpe}"

        # Verify trades occurred (should have quarterly rebalances)
        assert result.metrics.num_trades > 0, "Expected trades from rebalancing"
