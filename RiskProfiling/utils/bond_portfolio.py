from RiskProfiling.models import ETF, ETFPrice
from datetime import date
from .black_models import black_model_call_delta

def generate_bond_portfolio(etf, base_date, today, r, sigma, AUM, K=None):
    # 가격 정보 로딩
    base_price = ETFPrice.objects.filter(etf=etf, date=base_date).first()
    current_price = ETFPrice.objects.filter(etf=etf, date=today).first()

    if not base_price or not current_price:
        raise ValueError("가격 정보가 누락되었습니다.")

    if K is None:
        K = base_price.close

    F = current_price.close
    T = ((today - base_date).days + 0.0001) / 365

    delta = black_model_call_delta(F, K, T, r, sigma)

    # 포트폴리오 구성
    portfolio = []
    used_cash = 0
    max_weight = 0.25

    n_lt = int(delta / max_weight)
    remain_weight = delta - (n_lt * max_weight)

    # 장기 ETF 선택 및 매수
    lt_etfs = ETF.objects.filter(sub_strategy='10Y').order_by('expense_ratio')[:n_lt + 1]
    for i, bond_etf in enumerate(lt_etfs):
        price = ETFPrice.objects.filter(etf=bond_etf, date=today).first()
        if not price:
            continue
        weight = max_weight if i < n_lt else remain_weight
        weight = min(weight, max_weight)
        units = int((AUM * weight) / price.close)
        cost = units * price.close
        if units <= 0:
            continue
        portfolio.append((bond_etf.name, bond_etf.ticker, price.close, units, cost))
        used_cash += cost

    # 단기 ETF 선택
    remain_cash = AUM - used_cash
    st_etfs = ETF.objects.filter(sub_strategy='ShortTerm').order_by('expense_ratio')
    for st_etf in st_etfs:
        if remain_cash < 10000:
            break
        price = ETFPrice.objects.filter(etf=st_etf, date=today).first()
        if not price:
            continue

        # 단기 ETF에도 최대 비중 25% 적용
        max_st_units = int((AUM * max_weight) // price.close)
        units = min(int(remain_cash // price.close), max_st_units)
        cost = units * price.close
        if units <= 0:
            continue

        portfolio.append((st_etf.name, st_etf.ticker, price.close, units, cost))
        used_cash += cost
        remain_cash -= cost

    return {
        'delta': round(delta, 4),
        'F': F,
        'K': K,
        'T': round(T, 6),
        'portfolio': portfolio,
        'used_cash': round(used_cash)
    }
