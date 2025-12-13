"""Yearly Start Date Comparison Analysis.

Compare investment results when starting from different years.
"""

import pandas as pd
import yfinance as yf


def download_tqqq_data(start_date: str, end_date: str = "2024-12-31") -> pd.DataFrame:
    """Download TQQQ price data."""
    tqqq = yf.download(
        "TQQQ", start=start_date, end=end_date, progress=False, auto_adjust=True
    )
    return tqqq


def simulate_value_rebalancing(tqqq_data, initial_capital=10000):
    """Simulate Value Rebalancing strategy."""
    # Parameters (Michael Edleson / William Bernstein 권장값 + TQQQ 조정)
    value_growth_rate = 0.10  # 10% annual (Bernstein 7% 기준, TQQQ 조정)
    rebalance_frequency_days = 30  # Monthly

    # Initialize
    cash_pool = initial_capital
    stock_value = 0
    shares = 0

    start_date = tqqq_data.index[0]
    last_rebalance = None

    # Track history
    portfolio_values = []
    rebalance_dates = []
    actions = []

    for current_date in tqqq_data.index:
        current_price = float(tqqq_data.loc[current_date, "Close"])

        # Update stock value
        stock_value = shares * current_price
        current_total = stock_value + cash_pool

        # Calculate target value
        days_since_start = (current_date - start_date).days
        years = days_since_start / 365.0
        base_target = initial_capital * ((1 + value_growth_rate) ** years)
        target_stock_value = base_target * 0.8  # Target 80% in stocks

        # Check if rebalancing needed
        needs_rebalance = False
        if last_rebalance is None:
            needs_rebalance = True
        else:
            days_since_rebalance = (current_date - last_rebalance).days
            if days_since_rebalance >= rebalance_frequency_days:
                target_allocation = (
                    target_stock_value / current_total if current_total > 0 else 0.8
                )
                current_allocation = (
                    stock_value / current_total if current_total > 0 else 0
                )

                if abs(current_allocation - target_allocation) > 0.1:
                    needs_rebalance = True

        # Rebalance if needed
        action = "hold"
        if needs_rebalance:
            target_shares = (
                target_stock_value / current_price if current_price > 0 else 0
            )

            if stock_value > target_stock_value * 1.1:
                shares_to_sell = shares - target_shares
                if shares_to_sell > 0:
                    cash_from_sale = shares_to_sell * current_price * 0.999
                    cash_pool += cash_from_sale
                    shares = target_shares
                    action = "sell"

            elif stock_value < target_stock_value * 0.9:
                cash_needed = target_stock_value - stock_value
                cash_to_use = min(cash_needed, cash_pool * 0.95)
                if cash_to_use > 0:
                    shares_to_buy = (cash_to_use * 0.999) / current_price
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
            }
        )

    return {
        "final_value": total_value,
        "rebalance_count": len(rebalance_dates),
        "portfolio_values": pd.DataFrame(portfolio_values),
    }


def calculate_max_drawdown(values):
    """Calculate maximum drawdown."""
    cumulative = values / values.iloc[0]
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    return float(drawdown.min()) * 100


def analyze_year(start_year, end_date="2024-12-31", initial_capital=10000):
    """Analyze starting from a specific year."""
    start_date = f"{start_year}-01-01"

    # Download data
    tqqq = download_tqqq_data(start_date, end_date)

    if len(tqqq) == 0:
        return None

    # Basic stats
    start_price = float(tqqq["Close"].iloc[0])
    end_price = float(tqqq["Close"].iloc[-1])

    # Buy and hold
    bh_final_value = (initial_capital / start_price) * end_price
    bh_return = ((bh_final_value / initial_capital) - 1) * 100

    # Calculate buy-and-hold volatility and max drawdown
    daily_returns = tqqq["Close"].pct_change().dropna()
    daily_vol = float(daily_returns.std())
    bh_volatility = daily_vol * (252**0.5) * 100

    cumulative = (1 + daily_returns).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max
    bh_max_dd = float(drawdown.min()) * 100

    # Value rebalancing
    vr_result = simulate_value_rebalancing(tqqq, initial_capital)
    vr_final_value = vr_result["final_value"]
    vr_return = ((vr_final_value / initial_capital) - 1) * 100

    # Calculate VR volatility and max drawdown
    vr_values = vr_result["portfolio_values"]["total_value"]
    vr_daily_returns = vr_values.pct_change().dropna()
    vr_volatility = float(vr_daily_returns.std()) * (252**0.5) * 100
    vr_max_dd = calculate_max_drawdown(vr_values)

    # Calculate years
    years = len(tqqq) / 252

    return {
        "start_year": start_year,
        "start_date": tqqq.index[0].date(),
        "end_date": tqqq.index[-1].date(),
        "days": len(tqqq),
        "years": years,
        "start_price": start_price,
        "end_price": end_price,
        # Buy and Hold
        "bh_final_value": bh_final_value,
        "bh_return": bh_return,
        "bh_volatility": bh_volatility,
        "bh_max_dd": bh_max_dd,
        # Value Rebalancing
        "vr_final_value": vr_final_value,
        "vr_return": vr_return,
        "vr_volatility": vr_volatility,
        "vr_max_dd": vr_max_dd,
        "vr_rebalances": vr_result["rebalance_count"],
        # Comparison
        "excess_return": vr_return - bh_return,
        "volatility_reduction": bh_volatility - vr_volatility,
        "dd_improvement": bh_max_dd - vr_max_dd,
    }


def main():
    """Main function."""
    print("=" * 100)
    print("연도별 시작 시점 비교 분석 (TQQQ)")
    print("=" * 100)
    print("\n각 연도부터 시작했을 때의 성과 비교 (2024년 12월까지)")
    print()

    # Analyze each starting year
    years = [2019, 2020, 2021, 2022, 2023, 2024]
    results = []

    for year in years:
        print(f"분석 중: {year}년 시작...")
        result = analyze_year(year)
        if result:
            results.append(result)

    print("\n" + "=" * 100)
    print("분석 결과 요약")
    print("=" * 100)

    # Summary table
    print(
        f"\n{'시작연도':<8} {'기간':>6} {'BH 수익률':>12} {'VR 수익률':>12} {'초과수익':>10} {'리밸런싱':>10}"
    )
    print(f"{'-'*8} {'-'*6} {'-'*12} {'-'*12} {'-'*10} {'-'*10}")

    for r in results:
        print(
            f"{r['start_year']:<8} {r['years']:>5.1f}년 {r['bh_return']:>11.1f}% "
            f"{r['vr_return']:>11.1f}% {r['excess_return']:>9.1f}%p {r['vr_rebalances']:>9}회"
        )

    # Volatility comparison
    print(f"\n{'시작연도':<8} {'BH 변동성':>12} {'VR 변동성':>12} {'감소폭':>10}")
    print(f"{'-'*8} {'-'*12} {'-'*12} {'-'*10}")

    for r in results:
        print(
            f"{r['start_year']:<8} {r['bh_volatility']:>11.1f}% "
            f"{r['vr_volatility']:>11.1f}% {r['volatility_reduction']:>9.1f}%p"
        )

    # Max drawdown comparison
    print(f"\n{'시작연도':<8} {'BH 최대낙폭':>13} {'VR 최대낙폭':>13} {'개선폭':>10}")
    print(f"{'-'*8} {'-'*13} {'-'*13} {'-'*10}")

    for r in results:
        print(
            f"{r['start_year']:<8} {r['bh_max_dd']:>12.1f}% "
            f"{r['vr_max_dd']:>12.1f}% {r['dd_improvement']:>9.1f}%p"
        )

    # Detailed results
    print("\n" + "=" * 100)
    print("상세 분석")
    print("=" * 100)

    for r in results:
        print(f"\n【{r['start_year']}년 시작】")
        print(f"  기간: {r['start_date']} ~ {r['end_date']} ({r['years']:.1f}년)")
        print(f"  TQQQ 가격: ${r['start_price']:.2f} → ${r['end_price']:.2f}")
        print()
        print("  단순 보유 (Buy & Hold):")
        print(f"    - 최종 가치: ${r['bh_final_value']:,.2f}")
        print(f"    - 수익률: {r['bh_return']:+.1f}%")
        print(f"    - 변동성: {r['bh_volatility']:.1f}%")
        print(f"    - 최대낙폭: {r['bh_max_dd']:.1f}%")
        print()
        print("  밸류 리밸런싱:")
        print(f"    - 최종 가치: ${r['vr_final_value']:,.2f}")
        print(f"    - 수익률: {r['vr_return']:+.1f}%")
        print(f"    - 변동성: {r['vr_volatility']:.1f}%")
        print(f"    - 최대낙폭: {r['vr_max_dd']:.1f}%")
        print(f"    - 리밸런싱: {r['vr_rebalances']}회")
        print()
        print("  비교 (VR - BH):")
        print(f"    - 초과 수익: {r['excess_return']:+.1f}%p")
        print(f"    - 변동성 감소: {r['volatility_reduction']:+.1f}%p")
        print(f"    - 낙폭 개선: {r['dd_improvement']:+.1f}%p")

    # Key insights
    print("\n" + "=" * 100)
    print("핵심 인사이트")
    print("=" * 100)

    # Best year for each strategy
    best_bh = max(results, key=lambda x: x["bh_return"])
    best_vr = max(results, key=lambda x: x["vr_return"])
    best_excess = max(results, key=lambda x: x["excess_return"])

    print(
        f"\n최고 수익 (단순 보유): {best_bh['start_year']}년 시작 ({best_bh['bh_return']:+.1f}%)"
    )
    print(
        f"최고 수익 (밸류 리밸런싱): {best_vr['start_year']}년 시작 ({best_vr['vr_return']:+.1f}%)"
    )
    print(
        f"최고 초과 수익: {best_excess['start_year']}년 시작 ({best_excess['excess_return']:+.1f}%p)"
    )

    # Average improvements
    avg_volatility_reduction = sum(r["volatility_reduction"] for r in results) / len(
        results
    )
    avg_dd_improvement = sum(r["dd_improvement"] for r in results) / len(results)

    print(f"\n평균 변동성 감소: {avg_volatility_reduction:+.1f}%p")
    print(f"평균 낙폭 개선: {avg_dd_improvement:+.1f}%p")

    # When VR beats BH
    vr_wins = [r for r in results if r["excess_return"] > 0]

    if vr_wins:
        print("\n밸류 리밸런싱이 더 높은 수익을 낸 경우:")
        for r in vr_wins:
            print(f"  - {r['start_year']}년: {r['excess_return']:+.1f}%p 초과")
    else:
        print("\n모든 기간에서 단순 보유가 더 높은 수익")

    print("\n" + "=" * 100)
    print("분석 완료!")
    print("=" * 100)

    return results


if __name__ == "__main__":
    results = main()
