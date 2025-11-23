"""Core backtest execution engine."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
import pandas as pd

from ..models.backtest_config import BacktestConfiguration
from ..models.strategy import AllocationStrategy
from ..models.portfolio_state import PortfolioState
from ..models.trade import Trade
from ..models.performance import PerformanceMetrics
from ..models import RebalancingFrequency
from .exceptions import DataError
from . import metrics
from .rebalancer import generate_rebalancing_dates, calculate_rebalancing_trades


@dataclass
class BacktestResult:
    """Result of a backtest execution.

    Attributes:
        metrics: Performance metrics for the backtest
        trades: List of all trades executed
        portfolio_history: List of portfolio states over time
    """
    metrics: PerformanceMetrics
    trades: list[Trade]
    portfolio_history: list[PortfolioState]


class BacktestEngine:
    """Execute backtests for asset allocation strategies."""

    def run_backtest(
        self,
        config: BacktestConfiguration,
        strategy: AllocationStrategy,
        price_data: pd.DataFrame,
        exchange_rates: pd.DataFrame = None
    ) -> BacktestResult:
        """Run a complete backtest simulation.

        Args:
            config: Backtest configuration parameters
            strategy: Allocation strategy to test
            price_data: Historical price data
            exchange_rates: Optional exchange rate data for multi-currency

        Returns:
            BacktestResult with metrics, trades, and portfolio history

        Raises:
            DataError: If required price data is missing
        """
        # Initialize tracking
        trades = []
        portfolio_history = []

        # Get list of trading dates
        trading_dates = pd.to_datetime(price_data['date']).unique()
        trading_dates = sorted([d.date() for d in trading_dates])

        # Filter to backtest period
        trading_dates = [
            d for d in trading_dates
            if config.start_date <= d <= config.end_date
        ]

        if not trading_dates:
            raise DataError("No trading dates in backtest period")

        # Initialize portfolio on first day
        first_date = trading_dates[0]
        prices_first = self._get_prices_for_date(price_data, first_date, strategy)

        portfolio = self._initialize_portfolio(
            config.initial_capital,
            strategy,
            prices_first,
            first_date
        )

        # Record initial purchase trades
        for symbol, quantity in portfolio.asset_holdings.items():
            if quantity > 0:
                trade = Trade(
                    timestamp=first_date,
                    asset_symbol=symbol,
                    quantity=quantity,
                    price=prices_first[symbol],
                    currency=config.base_currency,
                    transaction_cost=Decimal("0")  # Initial purchase, no cost
                )
                trades.append(trade)

        # Record initial portfolio state
        portfolio_history.append(portfolio)

        # Generate rebalancing dates
        rebalancing_dates = generate_rebalancing_dates(
            config.start_date,
            config.end_date,
            config.rebalancing_frequency
        )
        # Remove first date (already handled in initialization)
        if rebalancing_dates and rebalancing_dates[0] == first_date:
            rebalancing_dates = rebalancing_dates[1:]

        # Simulate remaining days
        for current_date in trading_dates[1:]:
            # Get current prices
            current_prices = self._get_prices_for_date(
                price_data,
                current_date,
                strategy
            )

            # Update portfolio state with current prices
            portfolio = PortfolioState(
                timestamp=current_date,
                cash_balance=portfolio.cash_balance,
                asset_holdings=portfolio.asset_holdings.copy(),
                current_prices=current_prices
            )

            # Check if rebalancing is needed
            if current_date in rebalancing_dates:
                portfolio, rebalance_trades = self._rebalance_portfolio(
                    portfolio,
                    strategy,
                    config
                )
                trades.extend(rebalance_trades)

            # Record daily state
            portfolio_history.append(portfolio)

        # Calculate performance metrics
        performance_metrics = self._calculate_performance_metrics(
            portfolio_history,
            trades,
            config
        )

        return BacktestResult(
            metrics=performance_metrics,
            trades=trades,
            portfolio_history=portfolio_history
        )

    def _initialize_portfolio(
        self,
        initial_capital: Decimal,
        strategy: AllocationStrategy,
        initial_prices: dict[str, Decimal],
        timestamp: date
    ) -> PortfolioState:
        """Initialize portfolio by purchasing assets according to strategy weights.

        Args:
            initial_capital: Starting capital
            strategy: Allocation strategy
            initial_prices: Initial prices for all assets
            timestamp: Date of initialization

        Returns:
            Initial PortfolioState
        """
        asset_holdings = {}

        # Calculate how much to invest in each asset
        for symbol, weight in strategy.asset_weights.items():
            target_value = initial_capital * weight
            price = initial_prices[symbol]

            # Calculate quantity (support fractional shares)
            quantity = target_value / price

            # Round to 6 decimal places
            quantity = quantity.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

            asset_holdings[symbol] = quantity

        # Calculate remaining cash (should be minimal due to rounding)
        total_invested = sum(
            holdings * initial_prices[symbol]
            for symbol, holdings in asset_holdings.items()
        )
        cash_balance = initial_capital - total_invested

        # Round cash to 2 decimal places
        cash_balance = cash_balance.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return PortfolioState(
            timestamp=timestamp,
            cash_balance=cash_balance,
            asset_holdings=asset_holdings,
            current_prices=initial_prices
        )

    def _get_prices_for_date(
        self,
        price_data: pd.DataFrame,
        target_date: date,
        strategy: AllocationStrategy,
        max_lookback_days: int = 5
    ) -> dict[str, Decimal]:
        """Get prices for all assets on a specific date with forward-fill.

        If data is missing for target_date, looks back up to max_lookback_days
        to find the most recent available price.

        Args:
            price_data: Historical price DataFrame
            target_date: Date to get prices for
            strategy: Strategy (to know which symbols needed)
            max_lookback_days: Maximum days to look back for missing data

        Returns:
            Dictionary mapping symbol to price

        Raises:
            DataError: If price data missing for required symbols after forward-fill
        """
        prices = {}

        for symbol in strategy.asset_weights.keys():
            price_found = False

            # Try target date first, then look back up to max_lookback_days
            for days_back in range(max_lookback_days + 1):
                check_date = target_date - pd.Timedelta(days=days_back)
                check_ts = pd.Timestamp(check_date)

                symbol_data = price_data[
                    (price_data['date'] == check_ts) &
                    (price_data['symbol'] == symbol)
                ]

                if not symbol_data.empty:
                    price = Decimal(str(symbol_data.iloc[0]['price']))

                    # Round to 4 decimal places
                    price = price.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

                    prices[symbol] = price
                    price_found = True

                    if days_back > 0:
                        import logging
                        logging.warning(
                            f"Forward-filled {symbol} price: used {check_date} "
                            f"data for {target_date} ({days_back} days back)"
                        )

                    break

            if not price_found:
                raise DataError(
                    f"No price data for {symbol} on {target_date} "
                    f"(looked back {max_lookback_days} days)"
                )

        return prices

    def _calculate_performance_metrics(
        self,
        portfolio_history: list[PortfolioState],
        trades: list[Trade],
        config: BacktestConfiguration
    ) -> PerformanceMetrics:
        """Calculate performance metrics from portfolio history.

        Args:
            portfolio_history: List of portfolio states
            trades: List of trades executed
            config: Backtest configuration

        Returns:
            PerformanceMetrics
        """
        # Extract portfolio values
        portfolio_values = pd.Series([
            float(state.total_value) for state in portfolio_history
        ])

        # Calculate daily returns
        daily_returns = portfolio_values.pct_change().dropna()

        # Get start and end values
        start_value = portfolio_history[0].total_value
        end_value = portfolio_history[-1].total_value

        # Calculate metrics
        total_return = metrics.calculate_total_return(start_value, end_value)

        num_trading_days = len(portfolio_history) - 1
        annualized_return = metrics.calculate_annualized_return(
            total_return,
            num_trading_days
        )

        volatility = metrics.calculate_volatility(daily_returns)

        max_drawdown = metrics.calculate_max_drawdown(portfolio_values)

        # Calculate Sharpe ratio (handle zero volatility)
        try:
            sharpe_ratio = metrics.calculate_sharpe_ratio(
                annualized_return,
                volatility,
                config.risk_free_rate
            )
        except ZeroDivisionError:
            sharpe_ratio = Decimal("0")

        return PerformanceMetrics(
            total_return=total_return,
            annualized_return=annualized_return,
            volatility=volatility,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            num_trades=len(trades),
            start_date=config.start_date,
            end_date=config.end_date,
            start_value=start_value,
            end_value=end_value
        )

    def _rebalance_portfolio(
        self,
        current_state: PortfolioState,
        strategy: AllocationStrategy,
        config: BacktestConfiguration
    ) -> tuple[PortfolioState, list[Trade]]:
        """Rebalance portfolio to target weights.

        Args:
            current_state: Current portfolio state
            strategy: Target allocation strategy
            config: Backtest configuration

        Returns:
            Tuple of (new portfolio state, list of trades executed)
        """
        # Calculate required trades
        trade_quantities = calculate_rebalancing_trades(current_state, strategy)

        trades = []
        new_holdings = current_state.asset_holdings.copy()

        # Execute trades
        for symbol, quantity_change in trade_quantities.items():
            if abs(quantity_change) < Decimal("0.000001"):
                # Skip tiny trades
                continue

            # Calculate transaction cost
            trade_value = abs(quantity_change * current_state.current_prices[symbol])
            transaction_cost = self._calculate_trade_cost(trade_value, config.transaction_costs)

            # Create trade record
            trade = Trade(
                timestamp=current_state.timestamp,
                asset_symbol=symbol,
                quantity=quantity_change,
                price=current_state.current_prices[symbol],
                currency=config.base_currency,
                transaction_cost=transaction_cost
            )
            trades.append(trade)

            # Update holdings
            new_holdings[symbol] = new_holdings.get(symbol, Decimal("0")) + quantity_change

        # Create new portfolio state
        new_state = PortfolioState(
            timestamp=current_state.timestamp,
            cash_balance=current_state.cash_balance,
            asset_holdings=new_holdings,
            current_prices=current_state.current_prices
        )

        return new_state, trades

    def _calculate_trade_cost(
        self,
        trade_value: Decimal,
        transaction_costs: 'TransactionCosts'
    ) -> Decimal:
        """Calculate transaction cost for a trade.

        Formula: fixed_per_trade + (percentage × trade_value)

        Args:
            trade_value: Absolute value of trade
            transaction_costs: Transaction cost parameters

        Returns:
            Total transaction cost
        """
        fixed_cost = transaction_costs.fixed_per_trade
        percentage_cost = transaction_costs.percentage * trade_value

        total_cost = fixed_cost + percentage_cost

        # Round to 2 decimal places
        return total_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
