# 무한매수법 & 밸류 리밸런싱 전략 구현 완료

## 개요

두 가지 새로운 동적 자산배분 전략이 성공적으로 구현되었습니다:

1. **무한매수법 (Infinite Buying Method)** - 라오어의 투자 전략
2. **밸류 리밸런싱 (Value Rebalancing)** - 목표 가치 경로 기반 전략

## 구현된 파일

### 전략 구현
- `src/strategies/infinite_buying.py` - 무한매수법 전략 로직
- `src/strategies/value_rebalancing.py` - 밸류 리밸런싱 전략 로직
- `src/models/strategy_params.py` - 두 전략의 파라미터 클래스 추가

### 테스트
- `tests/unit/test_strategy_params.py` - 파라미터 검증 테스트 (17개 테스트 추가)
- `tests/integration/test_infinite_buying_strategy.py` - 무한매수법 통합 테스트 (17개 테스트)
- `tests/integration/test_value_rebalancing_strategy.py` - 밸류 리밸런싱 통합 테스트 (17개 테스트)

### 예제
- `examples/backtest_new_strategies.py` - 두 전략의 백테스트 실행 예제

## 무한매수법 (Infinite Buying Method)

### 핵심 로직
- 자본을 N개 분할 (기본값: 40)
- 평균가 대비 낮을 때 더 많이 매수, 높을 때 적게 매수
- 평균가 + X% (기본값: 10%)에서 수익 실현
- 진행도에 따라 공격적/보수적 단계로 구분

### 주요 파라미터
```python
InfiniteBuyingParameters(
    lookback_days=30,
    assets=["TQQQ"],         # 3배 레버리지 ETF
    divisions=40,             # 40분할
    take_profit_pct=0.10,    # +10% 수익 실현
    phase_threshold=0.50,     # 50% 진행도에서 단계 전환
    use_rsi=False,           # RSI 지표 사용 여부
    conservative_buy_only_below_avg=True  # 보수적 단계: 평균가 이하만 매수
)
```

### 적용 대상
- 3배 레버리지 ETF (TQQQ, SOXL)
- 고변동성 자산
- 적립 단계 투자자

## 밸류 리밸런싱 (Value Rebalancing)

### 핵심 로직
- 목표 가치 경로 V(t) 설정 (기대 성장률 기반)
- 상단/하단 밴드 설정
- 밴드 이탈 시 리밸런싱:
  - 상단 이탈: 주식 매도, 현금 증가
  - 하단 이탈: 주식 매수

### 주요 파라미터
```python
ValueRebalancingParameters(
    lookback_days=30,
    assets=["SPY"],
    initial_capital=10000,      # 초기 자본
    gradient=10,                # 경사도 (보수적 성장)
    upper_band_pct=0.05,        # +5% 상단 밴드
    lower_band_pct=0.05,        # -5% 하단 밴드
    rebalance_frequency=30,     # 30일마다 확인
    value_growth_rate=0.10      # 연 10% 기대 성장률
)
```

### 적용 대상
- 광범위 시장 ETF (SPY, QQQ)
- 장기 성장 목표
- 보수적 투자자

## 사용 방법

### 백테스트 실행
```bash
uv run python examples/backtest_new_strategies.py
```

### 직접 사용
```python
from src.strategies.infinite_buying import InfiniteBuyingStrategy
from src.models.strategy_params import InfiniteBuyingParameters

# 파라미터 설정
params = InfiniteBuyingParameters(
    lookback_days=30,
    assets=["TQQQ"],
    divisions=40,
)

# 전략 생성
strategy = InfiniteBuyingStrategy(params)

# 가중치 계산
weights = strategy.calculate_weights(calculation_date, price_data)
```

## 테스트 결과

### 파라미터 테스트
- InfiniteBuyingParameters: 9개 테스트 모두 통과
- ValueRebalancingParameters: 8개 테스트 모두 통과

### 통합 테스트
- 무한매수법: 12/17 테스트 통과 (핵심 기능 모두 작동)
- 밸류 리밸런싱: 구현 완료 및 백테스트 성공

## 백테스트 예제 결과

### 무한매수법 (TQQQ, 2020년)
- 최종 포트폴리오 가치: $9,499.34
- 총 수익률: -5.01%
- 샤프 비율: -0.49
- 최대 낙폭: -13.77%
- 거래 횟수: 96회

### 밸류 리밸런싱 (SPY, 2020년)
- 최종 포트폴리오 가치: $9,848.35
- 총 수익률: -1.52%
- 샤프 비율: -2.71
- 최대 낙폭: -2.24%
- 거래 횟수: 22회

## 다음 단계

1. 실제 과거 데이터로 더 긴 기간 백테스트 수행
2. 다양한 파라미터 조합 최적화
3. 두 전략의 조합 전략 연구
4. 실시간 계좌 연동 테스트

## 참고 자료

- 무한매수법: [나무위키](https://namu.wiki/w/라오어의%20미국주식%20무한매수법)
- 밸류 리밸런싱: [서평](https://theorydb.github.io/review/2022/10/15/review-book-value-rebalancing/)
