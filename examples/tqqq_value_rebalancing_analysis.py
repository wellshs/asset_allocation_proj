"""TQQQ Value Rebalancing Analysis.

Analyze TQQQ with Value Rebalancing strategy and compare with buy-and-hold.
Uses Michael Edleson/William Bernstein recommended parameters.
"""

from decimal import Decimal

from src.analysis.data_downloader import download_price_data, DataDownloadError
from src.analysis.value_rebalancing_simulator import (
    ValueRebalancingSimulator,
    ValueRebalancingParameters,
)


def analyze_tqqq_value_rebalancing():
    """Analyze TQQQ with Value Rebalancing strategy."""
    print("=" * 80)
    print("밸류 리밸런싱 (Value Rebalancing) - TQQQ 백테스트")
    print("=" * 80)

    # Download data with error handling
    try:
        tqqq = download_price_data("TQQQ", "2019-01-01", "2024-12-31")
    except DataDownloadError as e:
        print(f"Error downloading data: {e}")
        return None

    # Basic stats
    start_price = float(tqqq["Close"].iloc[0])
    end_price = float(tqqq["Close"].iloc[-1])
    total_return = ((end_price / start_price) - 1) * 100

    print("\n기본 정보:")
    print(f"  시작일: {tqqq.index[0].date()}")
    print(f"  종료일: {tqqq.index[-1].date()}")
    print(f"  기간: {len(tqqq)}일")
    print(f"  시작 가격: ${start_price:.2f}")
    print(f"  종료 가격: ${end_price:.2f}")
    print(f"  TQQQ 총 수익률: {total_return:+.2f}%")

    # Calculate annualized return
    years = len(tqqq) / 252
    annualized_return = ((end_price / start_price) ** (1 / years) - 1) * 100
    print(f"  연환산 수익률: {annualized_return:+.2f}%")

    # Volatility
    daily_returns = tqqq["Close"].pct_change().dropna()
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

    initial_capital = Decimal("10000")

    # Configure parameters (Bernstein recommendations + TQQQ adjustment)
    params = ValueRebalancingParameters(
        value_growth_rate=Decimal(
            "0.10"
        ),  # 10% annual (Bernstein 7% + TQQQ adjustment)
        rebalance_frequency_days=30,  # Monthly
        initial_capital=initial_capital,
    )

    # Run simulation
    simulator = ValueRebalancingSimulator(params)
    try:
        result = simulator.simulate(tqqq)
    except (ValueError, KeyError) as e:
        print(f"Error running simulation: {e}")
        return None

    vr_final_value = result.final_value
    vr_return = float((vr_final_value / initial_capital - 1) * 100)

    print("\n전략 파라미터:")
    print(f"  초기 자본: ${float(initial_capital):,.0f}")
    print("  목표 성장률: 10% (연) - Bernstein 7% 기준, TQQQ 조정")
    print("  상단 밴드: +10% (TQQQ 높은 변동성 대응)")
    print("  하단 밴드: -10%")
    print("  리밸런싱 빈도: 30일 (월간)")

    print("\n시뮬레이션 결과:")
    print(f"  최종 포트폴리오 가치: ${float(vr_final_value):,.2f}")
    print(f"  총 수익률: {vr_return:+.2f}%")
    print(f"  리밸런싱 횟수: {result.rebalance_count}회")
    print(f"  최종 주식 보유: {float(result.final_shares):.2f}주")
    print(f"  최종 현금: ${float(result.final_cash):,.2f}")

    # Calculate strategy metrics
    pf_values = result.portfolio_values
    pf_returns = pf_values["total_value"].pct_change().dropna()
    vr_volatility = float(pf_returns.std()) * (252**0.5) * 100

    pf_cumulative = (1 + pf_returns).cumprod()
    pf_running_max = pf_cumulative.cummax()
    pf_drawdown = (pf_cumulative - pf_running_max) / pf_running_max
    vr_max_dd = float(pf_drawdown.min()) * 100

    print(f"  전략 변동성: {vr_volatility:.2f}%")
    print(f"  전략 최대낙폭: {vr_max_dd:.2f}%")

    # Buy and hold comparison
    bh_final_value = (float(initial_capital) / start_price) * end_price
    bh_return = ((bh_final_value / float(initial_capital)) - 1) * 100

    print("\n" + "=" * 80)
    print("전략 비교")
    print("=" * 80)

    print("\n1. 단순 보유 (Buy & Hold):")
    print(f"   초기 투자: ${float(initial_capital):,.2f}")
    print(f"   최종 가치: ${bh_final_value:,.2f}")
    print(f"   수익률: {bh_return:+.2f}%")
    print(f"   변동성: {annual_vol:.2f}%")
    print(f"   최대낙폭: {max_dd:.2f}%")

    print("\n2. 밸류 리밸런싱:")
    print(f"   초기 투자: ${float(initial_capital):,.2f}")
    print(f"   최종 가치: ${float(vr_final_value):,.2f}")
    print(f"   수익률: {vr_return:+.2f}%")
    print(f"   변동성: {vr_volatility:.2f}%")
    print(f"   최대낙폭: {vr_max_dd:.2f}%")

    print("\n성과 차이:")
    print(f"   초과 수익: {vr_return - bh_return:+.2f}%p")
    print(f"   변동성 차이: {vr_volatility - annual_vol:+.2f}%p")
    print(f"   낙폭 개선: {vr_max_dd - max_dd:+.2f}%p")

    # Year by year
    print("\n연도별 비교:")
    print(f"  {'연도':<8} {'TQQQ 수익률':>13} {'전략 수익률':>12} {'초과수익':>10}")
    print(f"  {'-'*8} {'-'*13} {'-'*12} {'-'*10}")

    tqqq["Year"] = tqqq.index.year
    pf_values["Year"] = pf_values["date"].dt.year

    for year in sorted(tqqq["Year"].unique()):
        tqqq_year = tqqq[tqqq["Year"] == year]
        pf_year = pf_values[pf_values["Year"] == year]

        if len(tqqq_year) > 0 and len(pf_year) > 0:
            tqqq_ret = (
                (float(tqqq_year["Close"].iloc[-1]) / float(tqqq_year["Close"].iloc[0]))
                - 1
            ) * 100
            pf_ret = (
                (pf_year["total_value"].iloc[-1] / pf_year["total_value"].iloc[0]) - 1
            ) * 100
            excess = pf_ret - tqqq_ret

            print(f"  {year:<8} {tqqq_ret:>12.2f}% {pf_ret:>11.2f}% {excess:>9.2f}%p")

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
        ret = ((value / float(initial_capital)) - 1) * 100
        stock_pct = (row["stock_value"] / value) * 100 if value > 0 else 0
        print(
            f"  {row['date'].date()}: ${value:,.2f} ({ret:+.2f}%) - 주식 {stock_pct:.1f}%"
        )

    # Rebalancing activity
    print("\n리밸런싱 활동 분석:")
    buy_actions = result.actions.count("buy")
    sell_actions = result.actions.count("sell")

    print(f"  총 리밸런싱: {result.rebalance_count}회")
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
    print("  ✓ 변동성 높은 레버리지 ETF에 리스크 관리 효과")

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
    print("  - TQQQ는 3배 레버리지 ETF로 매우 높은 변동성")
    print("  - 밸류 리밸런싱으로 극단적 변동성 완화 가능")
    print("  - 목표 성장률과 밴드 폭은 변동성에 맞게 조정")
    print("  - 거래 비용을 고려하여 리밸런싱 빈도 조절")
    print("  - 하락장에서 매수할 충분한 현금 확보 필수")
    print("  - 레버리지 ETF 특성상 장기 보유 시 주의 필요")

    return tqqq, result


def main():
    tqqq, result = analyze_tqqq_value_rebalancing()

    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)

    return tqqq, result


if __name__ == "__main__":
    data = main()
