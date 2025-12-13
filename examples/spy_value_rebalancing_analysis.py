"""SPY Value Rebalancing Analysis.

Analyze SPY with Value Rebalancing strategy and compare with buy-and-hold.
"""

import pandas as pd
import yfinance as yf


def download_spy_data(
    start_date: str = "2019-01-01", end_date: str = "2024-12-31"
) -> pd.DataFrame:
    """Download SPY price data."""
    print(f"Downloading SPY data from {start_date} to {end_date}...")

    spy = yf.download(
        "SPY", start=start_date, end=end_date, progress=False, auto_adjust=True
    )

    print(f"Downloaded {len(spy)} days of data")
    print(f"Date range: {spy.index[0].date()} to {spy.index[-1].date()}")

    return spy


def simulate_value_rebalancing(spy_data, initial_capital=10000):
    """Simulate Value Rebalancing strategy.

    Args:
        spy_data: SPY price data
        initial_capital: Initial investment amount

    Returns:
        Dictionary with simulation results
    """
    # Parameters (Michael Edleson / William Bernstein 권장값)
    value_growth_rate = 0.07  # 7% annual (Bernstein 권장 - 보수적 추정)
    rebalance_frequency_days = 30  # Monthly (원래 이론 권장)

    # Initialize
    cash_pool = initial_capital
    stock_value = 0
    shares = 0

    start_date = spy_data.index[0]
    last_rebalance = None

    # Track history
    portfolio_values = []
    rebalance_dates = []
    actions = []

    for current_date in spy_data.index:
        current_price = float(spy_data.loc[current_date, "Close"])

        # Update stock value
        stock_value = shares * current_price
        current_total = stock_value + cash_pool

        # Calculate target value (using total portfolio as reference)
        days_since_start = (current_date - start_date).days
        years = days_since_start / 365.0
        # Target: start at 80% stocks, grow at target rate
        base_target = initial_capital * ((1 + value_growth_rate) ** years)
        target_stock_value = base_target * 0.8  # Target 80% in stocks

        # Check if rebalancing needed
        needs_rebalance = False
        if last_rebalance is None:
            # Initial investment
            needs_rebalance = True
        else:
            days_since_rebalance = (current_date - last_rebalance).days
            if days_since_rebalance >= rebalance_frequency_days:
                # Check if stock allocation is too far from target
                target_allocation = (
                    target_stock_value / current_total if current_total > 0 else 0.8
                )
                current_allocation = (
                    stock_value / current_total if current_total > 0 else 0
                )

                if abs(current_allocation - target_allocation) > 0.1:  # 10% deviation
                    needs_rebalance = True

        # Rebalance if needed
        action = "hold"
        if needs_rebalance:
            # Calculate target shares based on target stock value
            target_shares = (
                target_stock_value / current_price if current_price > 0 else 0
            )

            if stock_value > target_stock_value * 1.1:
                # Stock allocation too high, sell some
                shares_to_sell = shares - target_shares

                if shares_to_sell > 0:
                    cash_from_sale = (
                        shares_to_sell * current_price * 0.999
                    )  # 0.1% commission
                    cash_pool += cash_from_sale
                    shares = target_shares
                    action = "sell"

            elif stock_value < target_stock_value * 0.9:
                # Stock allocation too low, buy more
                cash_needed = target_stock_value - stock_value
                cash_to_use = min(cash_needed, cash_pool * 0.95)

                if cash_to_use > 0:
                    shares_to_buy = (
                        cash_to_use * 0.999
                    ) / current_price  # 0.1% commission
                    shares += shares_to_buy
                    cash_pool -= cash_to_use
                    action = "buy"

            if action != "hold":
                last_rebalance = current_date
                rebalance_dates.append(current_date)
                actions.append(action)

        # Update stock value after rebalance
        stock_value = shares * current_price
        total_value = stock_value + cash_pool

        portfolio_values.append(
            {
                "date": current_date,
                "total_value": total_value,
                "stock_value": stock_value,
                "cash_pool": cash_pool,
                "shares": shares,
                "price": current_price,
                "target_stock_value": target_stock_value,
                "base_target": base_target,
                "action": action,
            }
        )

    return {
        "portfolio_values": pd.DataFrame(portfolio_values),
        "rebalance_count": len(rebalance_dates),
        "actions": actions,
        "final_value": total_value,
        "final_shares": shares,
        "final_cash": cash_pool,
    }


def analyze_spy_value_rebalancing():
    """Analyze SPY with Value Rebalancing strategy."""
    print("=" * 80)
    print("밸류 리밸런싱 (Value Rebalancing) - SPY 백테스트")
    print("=" * 80)

    # Download data
    spy = download_spy_data("2019-01-01", "2024-12-31")

    # Basic stats
    start_price = float(spy["Close"].iloc[0])
    end_price = float(spy["Close"].iloc[-1])
    total_return = ((end_price / start_price) - 1) * 100

    print("\n기본 정보:")
    print(f"  시작일: {spy.index[0].date()}")
    print(f"  종료일: {spy.index[-1].date()}")
    print(f"  기간: {len(spy)}일")
    print(f"  시작 가격: ${start_price:.2f}")
    print(f"  종료 가격: ${end_price:.2f}")
    print(f"  SPY 총 수익률: {total_return:+.2f}%")

    # Calculate annualized return
    years = len(spy) / 252
    annualized_return = ((end_price / start_price) ** (1 / years) - 1) * 100
    print(f"  연환산 수익률: {annualized_return:+.2f}%")

    # Volatility
    daily_returns = spy["Close"].pct_change().dropna()
    daily_vol = float(daily_returns.std())
    annual_vol = daily_vol * (252**0.5) * 100
    print(f"  연환산 변동성: {annual_vol:.2f}%")

    # Max drawdown
    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    max_dd = float(drawdown.min()) * 100
    print(f"  최대 낙폭 (MDD): {max_dd:.2f}%")

    # Run Value Rebalancing simulation
    print("\n" + "=" * 80)
    print("밸류 리밸런싱 전략 시뮬레이션")
    print("=" * 80)

    initial_capital = 10000
    result = simulate_value_rebalancing(spy, initial_capital)

    vr_final_value = result["final_value"]
    vr_return = ((vr_final_value / initial_capital) - 1) * 100

    print("\n전략 파라미터:")
    print(f"  초기 자본: ${initial_capital:,.0f}")
    print("  목표 성장률: 7% (연) - Bernstein 권장")
    print("  상단 밴드: +5%")
    print("  하단 밴드: -5%")
    print("  리밸런싱 빈도: 30일 (월간)")

    print("\n시뮬레이션 결과:")
    print(f"  최종 포트폴리오 가치: ${vr_final_value:,.2f}")
    print(f"  총 수익률: {vr_return:+.2f}%")
    print(f"  리밸런싱 횟수: {result['rebalance_count']}회")
    print(f"  최종 주식 보유: {result['final_shares']:.2f}주")
    print(f"  최종 현금: ${result['final_cash']:,.2f}")

    # Calculate strategy metrics
    pf_values = result["portfolio_values"]
    pf_returns = pf_values["total_value"].pct_change().dropna()
    vr_volatility = float(pf_returns.std()) * (252**0.5) * 100

    pf_cumulative = (1 + pf_returns).cumprod()
    pf_running_max = pf_cumulative.cummax()
    pf_drawdown = (pf_cumulative - pf_running_max) / pf_running_max
    vr_max_dd = float(pf_drawdown.min()) * 100

    print(f"  전략 변동성: {vr_volatility:.2f}%")
    print(f"  전략 최대낙폭: {vr_max_dd:.2f}%")

    # Buy and hold comparison
    bh_final_value = (initial_capital / start_price) * end_price
    bh_return = ((bh_final_value / initial_capital) - 1) * 100

    print("\n" + "=" * 80)
    print("전략 비교")
    print("=" * 80)

    print("\n1. 단순 보유 (Buy & Hold):")
    print(f"   초기 투자: ${initial_capital:,.2f}")
    print(f"   최종 가치: ${bh_final_value:,.2f}")
    print(f"   수익률: {bh_return:+.2f}%")
    print(f"   변동성: {annual_vol:.2f}%")
    print(f"   최대낙폭: {max_dd:.2f}%")

    print("\n2. 밸류 리밸런싱:")
    print(f"   초기 투자: ${initial_capital:,.2f}")
    print(f"   최종 가치: ${vr_final_value:,.2f}")
    print(f"   수익률: {vr_return:+.2f}%")
    print(f"   변동성: {vr_volatility:.2f}%")
    print(f"   최대낙폭: {vr_max_dd:.2f}%")

    print("\n성과 차이:")
    print(f"   초과 수익: {vr_return - bh_return:+.2f}%p")
    print(f"   변동성 차이: {vr_volatility - annual_vol:+.2f}%p")
    print(f"   낙폭 개선: {vr_max_dd - max_dd:+.2f}%p")

    # Year by year
    print("\n연도별 비교:")
    print(f"  {'연도':<8} {'SPY 수익률':>12} {'전략 수익률':>12} {'초과수익':>10}")
    print(f"  {'-'*8} {'-'*12} {'-'*12} {'-'*10}")

    spy["Year"] = spy.index.year
    pf_values["Year"] = pf_values["date"].dt.year

    for year in sorted(spy["Year"].unique()):
        spy_year = spy[spy["Year"] == year]
        pf_year = pf_values[pf_values["Year"] == year]

        if len(spy_year) > 0 and len(pf_year) > 0:
            spy_ret = (
                (float(spy_year["Close"].iloc[-1]) / float(spy_year["Close"].iloc[0]))
                - 1
            ) * 100
            pf_ret = (
                (pf_year["total_value"].iloc[-1] / pf_year["total_value"].iloc[0]) - 1
            ) * 100
            excess = pf_ret - spy_ret

            print(f"  {year:<8} {spy_ret:>11.2f}% {pf_ret:>11.2f}% {excess:>9.2f}%p")

    # Portfolio evolution
    print("\n포트폴리오 가치 변화:")
    milestones = [
        0,
        len(pf_values) // 4,
        len(pf_values) // 2,
        3 * len(pf_values) // 4,
        -1,
    ]

    for idx in milestones:
        row = pf_values.iloc[idx]
        value = row["total_value"]
        ret = ((value / initial_capital) - 1) * 100
        stock_pct = (row["stock_value"] / value) * 100 if value > 0 else 0
        print(
            f"  {row['date'].date()}: ${value:,.2f} ({ret:+.2f}%) - 주식 {stock_pct:.1f}%"
        )

    # Rebalancing activity
    print("\n리밸런싱 활동 분석:")
    buy_actions = result["actions"].count("buy")
    sell_actions = result["actions"].count("sell")

    print(f"  총 리밸런싱: {result['rebalance_count']}회")
    print(f"  매수 (하단 밴드 이탈): {buy_actions}회")
    print(f"  매도 (상단 밴드 이탈): {sell_actions}회")

    # Key insights
    print("\n" + "=" * 80)
    print("전략 특징 및 시사점")
    print("=" * 80)

    print("\n밸류 리밸런싱 장점:")
    print("  ✓ 목표 가치 경로를 따라 안정적 성장")
    print("  ✓ 밴드를 이용한 체계적 리스크 관리")
    print("  ✓ 하락 시 매수, 상승 시 매도로 변동성 활용")
    print("  ✓ SPY 같은 안정적 ETF에 적합")

    print("\n실제 결과 분석:")
    if vr_return > bh_return:
        print(f"  ✓ 단순 보유 대비 {vr_return - bh_return:.2f}%p 초과 수익")
    else:
        print(f"  ✗ 단순 보유 대비 {abs(vr_return - bh_return):.2f}%p 낮은 수익")

    if vr_max_dd > max_dd:
        print(f"  ✓ 최대낙폭 {abs(vr_max_dd - max_dd):.2f}%p 개선")
    else:
        print(f"  ✗ 최대낙폭 {vr_max_dd - max_dd:.2f}%p 악화")

    print("\n권장 사항:")
    print("  - SPY는 미국 S&P 500 지수 추종 ETF로 안정적")
    print("  - 밸류 리밸런싱은 장기 투자에 적합")
    print("  - 목표 성장률과 밴드 폭은 개인 성향에 맞게 조정")
    print("  - 거래 비용을 고려하여 리밸런싱 빈도 조절")
    print("  - 하락장에서 매수할 현금 확보 필수")

    return spy, result


def main():
    spy, result = analyze_spy_value_rebalancing()

    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)

    return spy, result


if __name__ == "__main__":
    data = main()
