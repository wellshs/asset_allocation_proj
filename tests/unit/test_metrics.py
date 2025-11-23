"""Unit tests for performance metric calculations."""

import pytest
import numpy as np
import pandas as pd
from decimal import Decimal

from src.backtesting import metrics


class TestMetricCalculations:
    """Tests for performance metric calculation functions."""

    def test_total_return(self):
        """Test total return calculation."""
        initial = Decimal("100000")
        final = Decimal("150000")

        result = metrics.calculate_total_return(initial, final)

        # Expected: (150000 - 100000) / 100000 = 0.5 = 50%
        assert result == Decimal("0.5")

    def test_total_return_negative(self):
        """Test total return with loss."""
        initial = Decimal("100000")
        final = Decimal("80000")

        result = metrics.calculate_total_return(initial, final)

        # Expected: (80000 - 100000) / 100000 = -0.2 = -20%
        assert result == Decimal("-0.2")

    def test_annualized_return(self):
        """Test annualized return calculation."""
        total_return = Decimal("1.0")  # 100% total return
        num_days = 504  # ~2 years of trading days

        result = metrics.calculate_annualized_return(total_return, num_days)

        # Expected: (1 + 1.0)^(252/504) - 1 = 2^0.5 - 1 ≈ 0.4142 = 41.42%
        expected = Decimal("0.4142")
        assert abs(result - expected) < Decimal("0.01")

    def test_volatility(self):
        """Test annualized volatility calculation."""
        # Daily returns with known std dev
        daily_returns = pd.Series([0.01, -0.01, 0.02, -0.015, 0.005])

        result = metrics.calculate_volatility(daily_returns)

        # Expected: std(daily_returns) * sqrt(252)
        daily_std = Decimal(str(daily_returns.std()))
        expected = daily_std * Decimal(str(np.sqrt(252)))

        assert abs(result - expected) < Decimal("0.001")

    def test_max_drawdown(self):
        """Test maximum drawdown calculation."""
        # Portfolio values: peak at 120, trough at 80
        portfolio_values = pd.Series([100, 110, 120, 100, 80, 90, 110])

        result = metrics.calculate_max_drawdown(portfolio_values)

        # Expected: (80 - 120) / 120 = -0.3333 = -33.33%
        expected = Decimal("-0.3333")
        assert abs(result - expected) < Decimal("0.01")

    def test_max_drawdown_no_decline(self):
        """Test max drawdown when portfolio only increases."""
        portfolio_values = pd.Series([100, 110, 120, 130, 140])

        result = metrics.calculate_max_drawdown(portfolio_values)

        # Expected: 0 (no drawdown)
        assert result == Decimal("0")

    def test_sharpe_ratio(self):
        """Test Sharpe ratio calculation."""
        annualized_return = Decimal("0.12")  # 12%
        volatility = Decimal("0.15")  # 15%
        risk_free_rate = Decimal("0.02")  # 2%

        result = metrics.calculate_sharpe_ratio(
            annualized_return, volatility, risk_free_rate
        )

        # Expected: (0.12 - 0.02) / 0.15 = 0.6667
        expected = Decimal("0.67")
        assert abs(result - expected) < Decimal("0.01")

    def test_sharpe_ratio_zero_volatility(self):
        """Test Sharpe ratio when volatility is zero."""
        annualized_return = Decimal("0.05")
        volatility = Decimal("0")
        risk_free_rate = Decimal("0.02")

        # Should handle division by zero gracefully
        with pytest.raises(ZeroDivisionError):
            metrics.calculate_sharpe_ratio(
                annualized_return, volatility, risk_free_rate
            )
