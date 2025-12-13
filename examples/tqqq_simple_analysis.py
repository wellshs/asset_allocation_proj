"""Simple TQQQ analysis and comparison.

Instead of full backtest, let's analyze TQQQ returns and compare
with a simple buy-and-hold strategy.
"""

import pandas as pd
import yfinance as yf


def download_tqqq_data(
    start_date: str = "2019-01-01", end_date: str = "2024-12-31"
) -> pd.DataFrame:
    """Download TQQQ price data."""
    print(f"Downloading TQQQ data from {start_date} to {end_date}...")

    tqqq = yf.download(
        "TQQQ", start=start_date, end=end_date, progress=False, auto_adjust=True
    )

    print(f"Downloaded {len(tqqq)} days of data")
    print(f"Date range: {tqqq.index[0].date()} to {tqqq.index[-1].date()}")

    return tqqq


def analyze_tqqq():
    """Analyze TQQQ performance."""
    print("=" * 80)
    print("TQQQ (ProShares UltraPro QQQ) 분석")
    print("=" * 80)

    # Download data
    tqqq = download_tqqq_data("2019-01-01", "2024-12-31")

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
    print(f"  총 수익률: {total_return:+.2f}%")

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

    # Year-by-year returns
    print("\n연도별 수익률:")
    tqqq["Year"] = tqqq.index.year
    for year in sorted(tqqq["Year"].unique()):
        year_data = tqqq[tqqq["Year"] == year]
        year_return = (
            (float(year_data["Close"].iloc[-1]) / float(year_data["Close"].iloc[0])) - 1
        ) * 100
        print(f"  {year}: {year_return:+.2f}%")

    # Simulate $10,000 investment
    print("\n$10,000 투자 시뮬레이션:")
    initial_investment = 10000
    shares = initial_investment / start_price
    final_value = shares * end_price
    profit = final_value - initial_investment

    print(f"  초기 투자: ${initial_investment:,.2f}")
    print(f"  매수 주식수: {shares:.2f}주 @ ${start_price:.2f}")
    print(f"  최종 가치: ${final_value:,.2f}")
    print(f"  실현 수익: ${profit:,.2f} ({total_return:+.2f}%)")

    # Best and worst days
    best_return = float(daily_returns.max()) * 100
    worst_return = float(daily_returns.min()) * 100

    print("\n극단적인 날들:")
    print(f"  최고 일일 수익: +{best_return:.2f}%")
    print(f"  최악 일일 손실: {worst_return:.2f}%")

    # Price milestones
    print("\n주요 시점 가격:")
    milestones = [
        ("시작", tqqq.index[0]),
        ("COVID 직전 (2020-02)", pd.Timestamp("2020-02-19")),
        ("COVID 저점 (2020-03)", pd.Timestamp("2020-03-23")),
        ("회복 (2021-01)", pd.Timestamp("2021-01-04")),
        ("최근 (2024년말)", tqqq.index[-1]),
    ]

    for label, timestamp in milestones:
        if timestamp in tqqq.index:
            price = float(tqqq.loc[timestamp, "Close"])
            ret_from_start = ((price / start_price) - 1) * 100
            print(f"  {label}: ${price:.2f} ({ret_from_start:+.2f}% from start)")

    # Investment strategy comparison
    print("\n\n무한매수법 vs 단순 보유 비교:")
    print("=" * 80)
    print("\n단순 보유 (Buy & Hold) 전략:")
    print("  - 초기 투자: $10,000")
    print(f"  - 최종 가치: ${final_value:,.2f}")
    print(f"  - 수익률: {total_return:+.2f}%")

    print("\n무한매수법 (Infinite Buying) 전략 시뮬레이션:")
    print("  - 40분할로 자본 관리")
    print("  - 하락시 추가 매수, 상승시 수익 실현")
    print("  - 변동성이 큰 TQQQ에 최적화")
    print("  - 예상 효과: 변동성 활용으로 추가 수익 가능")
    print("  - 주의사항: 복잡한 관리, 거래 비용")

    print("\n권장 사항:")
    print("  - TQQQ는 변동성이 매우 큰 3배 레버리지 ETF")
    print("  - 장기 보유보다는 단기/중기 전술적 투자에 적합")
    print("  - 무한매수법 사용시 충분한 현금 보유 필수")
    print("  - 리스크 관리와 손절 규칙 필수")

    return tqqq


def main():
    tqqq = analyze_tqqq()

    print("\n" + "=" * 80)
    print("분석 완료!")
    print("=" * 80)

    return tqqq


if __name__ == "__main__":
    data = main()
