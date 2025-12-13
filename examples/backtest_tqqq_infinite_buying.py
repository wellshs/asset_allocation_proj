"""Backtest Infinite Buying Method with real TQQQ data.

This script downloads real TQQQ historical data and runs a comprehensive
backtest of the Infinite Buying Method (무한매수법).
"""

from datetime import date
from decimal import Decimal
import pandas as pd
import yfinance as yf

from src.backtesting.engine import BacktestEngine
from src.models.backtest_config import BacktestConfiguration, TransactionCosts
from src.models import RebalancingFrequency
from src.strategies.infinite_buying import InfiniteBuyingStrategy
from src.models.strategy_params import InfiniteBuyingParameters


def download_tqqq_data(
    start_date: str = "2020-01-01", end_date: str = "2024-12-31"
) -> pd.DataFrame:
    """Download TQQQ price data from Yahoo Finance.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        DataFrame with TQQQ price data
    """
    print(f"Downloading TQQQ data from {start_date} to {end_date}...")

    # Download TQQQ data
    tqqq = yf.download(
        "TQQQ", start=start_date, end=end_date, progress=False, auto_adjust=True
    )

    # Create TQQQ dataframe
    tqqq_records = []
    for idx in range(len(tqqq)):
        tqqq_records.append(
            {
                "date": tqqq.index[idx],
                "symbol": "TQQQ",
                "price": float(tqqq["Close"].iloc[idx]),
                "currency": "USD",
            }
        )

    # Create CASH dataframe
    cash_records = []
    for idx in range(len(tqqq)):
        cash_records.append(
            {
                "date": tqqq.index[idx],
                "symbol": "CASH",
                "price": 1.0,
                "currency": "USD",
            }
        )

    # Combine
    all_records = tqqq_records + cash_records
    price_data = pd.DataFrame(all_records)

    print(f"Downloaded {len(tqqq)} days of data")
    print(f"Date range: {tqqq.index[0].date()} to {tqqq.index[-1].date()}")
    print(f"Starting price: ${float(tqqq['Close'].iloc[0]):.2f}")
    print(f"Ending price: ${float(tqqq['Close'].iloc[-1]):.2f}")
    print(
        f"Return: {((float(tqqq['Close'].iloc[-1]) / float(tqqq['Close'].iloc[0])) - 1) * 100:.2f}%"
    )

    return price_data


def run_backtest(
    price_data: pd.DataFrame,
    initial_capital: Decimal = Decimal("10000"),
    divisions: int = 40,
    take_profit_pct: Decimal = Decimal("0.10"),
    phase_threshold: Decimal = Decimal("0.50"),
    rebalance_frequency: RebalancingFrequency = RebalancingFrequency.WEEKLY,
    start_date: date = None,
    end_date: date = None,
):
    """Run backtest with specified parameters.

    Args:
        price_data: Historical price data
        initial_capital: Initial investment amount
        divisions: Number of capital divisions
        take_profit_pct: Take profit percentage
        phase_threshold: Phase switching threshold
        rebalance_frequency: Rebalancing frequency
        start_date: Backtest start date (None = auto)
        end_date: Backtest end date (None = auto)
    """
    # Auto-determine dates if not provided
    if start_date is None:
        # Start 60 days after first data point (need lookback)
        first_date = price_data[price_data["symbol"] == "TQQQ"]["date"].min()
        start_date = (first_date + pd.Timedelta(days=60)).date()

    if end_date is None:
        end_date = price_data[price_data["symbol"] == "TQQQ"]["date"].max().date()

    print("\n" + "=" * 80)
    print("무한매수법 (Infinite Buying Method) - TQQQ 백테스트")
    print("=" * 80)

    # Configure strategy parameters
    params = InfiniteBuyingParameters(
        lookback_days=30,
        assets=["TQQQ"],
        divisions=divisions,
        take_profit_pct=take_profit_pct,
        phase_threshold=phase_threshold,
        use_rsi=False,
        conservative_buy_only_below_avg=True,
    )
    params.validate()

    print("\n전략 파라미터:")
    print(f"  초기 자본: ${float(initial_capital):,.0f}")
    print(f"  분할 횟수: {divisions}")
    print(f"  수익 실현: +{float(take_profit_pct) * 100:.0f}%")
    print(f"  단계 전환: {float(phase_threshold) * 100:.0f}% 진행도")
    print(f"  리밸런싱: {rebalance_frequency.value}")

    # Create strategy
    strategy = InfiniteBuyingStrategy(params)

    # Configure backtest
    config = BacktestConfiguration(
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        rebalancing_frequency=rebalance_frequency,
        transaction_costs=TransactionCosts(
            fixed_per_trade=Decimal("1.0"),  # $1 per trade
            percentage=Decimal("0.001"),  # 0.1% commission
        ),
        base_currency="USD",
        risk_free_rate=Decimal("0.02"),  # 2% annual
    )

    print(f"\n백테스트 기간: {start_date} ~ {end_date}")

    # Run backtest
    engine = BacktestEngine()
    result = engine.run_backtest(config, strategy, price_data)

    # Display results
    print("\n" + "=" * 80)
    print("백테스트 결과")
    print("=" * 80)

    final_value = result.portfolio_history[-1].total_value
    total_return = float(result.metrics.total_return) * 100
    annual_return = float(result.metrics.annualized_return) * 100
    sharpe = float(result.metrics.sharpe_ratio)
    max_dd = float(result.metrics.max_drawdown) * 100

    print(f"\n최종 포트폴리오 가치: ${float(final_value):,.2f}")
    print(f"총 수익률: {total_return:+.2f}%")
    print(f"연환산 수익률: {annual_return:+.2f}%")
    print(f"샤프 비율: {sharpe:.2f}")
    print(f"최대 낙폭 (MDD): {max_dd:.2f}%")
    print(f"총 거래 횟수: {len(result.trades)}회")

    # Calculate buy-and-hold comparison
    tqqq_data = price_data[price_data["symbol"] == "TQQQ"].copy()
    tqqq_data = tqqq_data[
        (tqqq_data["date"] >= pd.Timestamp(start_date))
        & (tqqq_data["date"] <= pd.Timestamp(end_date))
    ]

    if len(tqqq_data) > 0:
        start_price = tqqq_data["price"].iloc[0]
        end_price = tqqq_data["price"].iloc[-1]
        bnh_return = ((end_price / start_price) - 1) * 100

        print(f"\nTQQQ 단순 보유 수익률: {bnh_return:+.2f}%")
        print(f"초과 수익: {total_return - bnh_return:+.2f}%p")

    # Transaction analysis
    total_commission = sum(float(t.transaction_cost) for t in result.trades)
    buy_trades = [
        t for t in result.trades if t.quantity > 0 and t.asset_symbol == "TQQQ"
    ]
    sell_trades = [
        t for t in result.trades if t.quantity < 0 and t.asset_symbol == "TQQQ"
    ]

    print("\n거래 분석:")
    print(f"  매수 거래: {len(buy_trades)}회")
    print(f"  매도 거래: {len(sell_trades)}회")
    print(f"  총 수수료: ${total_commission:,.2f}")

    # Show sample trades
    print("\n최근 거래 내역 (최근 10건):")
    for trade in result.trades[-10:]:
        if trade.asset_symbol == "TQQQ":
            action = "매수" if trade.quantity > 0 else "매도"
            qty = abs(float(trade.quantity))
            price = float(trade.price)
            total = qty * price
            print(
                f"  {trade.timestamp}: {action} {qty:.2f}주 @ ${price:.2f} = ${total:.2f}"
            )

    # Portfolio evolution
    print("\n포트폴리오 가치 변화:")
    milestones = [
        0,
        len(result.portfolio_history) // 4,
        len(result.portfolio_history) // 2,
        3 * len(result.portfolio_history) // 4,
        -1,
    ]

    for idx in milestones:
        state = result.portfolio_history[idx]
        value = float(state.total_value)
        ret = ((value / float(initial_capital)) - 1) * 100
        print(f"  {state.timestamp}: ${value:,.2f} ({ret:+.2f}%)")

    return result


def main():
    """Main function."""
    print("=" * 80)
    print("TQQQ 무한매수법 백테스트")
    print("=" * 80)

    # Download data (5 years)
    price_data = download_tqqq_data(start_date="2019-01-01", end_date="2024-12-31")

    # Run backtest with default parameters
    result = run_backtest(
        price_data=price_data,
        initial_capital=Decimal("10000"),
        divisions=40,
        take_profit_pct=Decimal("0.10"),
        phase_threshold=Decimal("0.50"),
        rebalance_frequency=RebalancingFrequency.WEEKLY,
    )

    print("\n" + "=" * 80)
    print("백테스트 완료!")
    print("=" * 80)

    return result


if __name__ == "__main__":
    result = main()
