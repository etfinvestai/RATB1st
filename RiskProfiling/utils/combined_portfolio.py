from datetime import datetime
from RiskProfiling.models import ETF, ETFPrice
from .strategy_portfolio import generate_strategy_portfolio
from .black_models import black_model_call_delta


def generate_combined_portfolio(base_date_str, total_invest, delta_date_str, r, sigma, K=None):
    base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
    delta_date = datetime.strptime(delta_date_str, "%Y-%m-%d").date()
    half_invest = total_invest / 2
    portfolio = []

    # -----------------------------------------------
    # 1. 주식형 포트폴리오 (전략 + RSI 기반)
    # -----------------------------------------------
    equity_portfolio = generate_strategy_portfolio(delta_date, half_invest)
    for item in equity_portfolio:
        item['type'] = '주식형'
        portfolio.append(item)

    # 주식형: 현금이 10,000원 이하가 될 때까지 순환하며 한 주씩 추가 매수
    equity_cash = half_invest - sum(p['cost'] for p in equity_portfolio)
    i = 0
    while equity_cash > 10000 and equity_portfolio:
        item = equity_portfolio[i % len(equity_portfolio)]
        if equity_cash >= item['price']:
            item['units'] += 1
            item['cost'] += item['price']
            equity_cash -= item['price']
        i += 1

    # -----------------------------------------------
    # 2. 채권형 포트폴리오 (델타 기반: 국고채 + MMF)
    # -----------------------------------------------
    bond_etf = ETF.objects.filter(name__icontains='국고채10년').first()
    if not bond_etf:
        raise ValueError("국고채 ETF를 찾을 수 없습니다.")

    bond_price_base = ETFPrice.objects.filter(etf=bond_etf, date=base_date).first()
    bond_price_today = ETFPrice.objects.filter(etf=bond_etf, date=delta_date).first()
    if not bond_price_base or not bond_price_today:
        raise ValueError("국고채 ETF 가격 정보가 없습니다.")

    F = bond_price_today.close
    T = ((delta_date - base_date).days + 0.0001) / 365
    if K is None:
        K = bond_price_base.close

    delta = black_model_call_delta(F, K, T, r, sigma)
    if delta is None:
        raise ValueError("델타 계산 실패")

    bond_weight = min(delta, 1.0)
    mmf_weight = max(1.0 - bond_weight, 0)

    # 국고채 ETF 매수
    bond_units = int((half_invest * bond_weight) / bond_price_today.close)
    bond_cost = bond_units * bond_price_today.close
    bond_entry = {
        'type': '채권형',
        'name': bond_etf.name,
        'ticker': bond_etf.ticker,
        'price': bond_price_today.close,
        'units': bond_units,
        'cost': bond_cost
    }
    portfolio.append(bond_entry)

    # 머니마켓 ETF 매수
    mmf_etf = ETF.objects.filter(name__icontains='머니마켓').first()
    if not mmf_etf:
        raise ValueError("머니마켓 ETF를 찾을 수 없습니다.")

    mmf_price = ETFPrice.objects.filter(etf=mmf_etf, date=base_date).first()
    if not mmf_price or mmf_price.close == 0:
        raise ValueError("머니마켓 ETF 가격 정보가 없습니다.")

    mmf_units = int((half_invest * mmf_weight) / mmf_price.close)
    mmf_cost = mmf_units * mmf_price.close
    mmf_entry = {
        'type': '채권형',
        'name': mmf_etf.name,
        'ticker': mmf_etf.ticker,
        'price': mmf_price.close,
        'units': mmf_units,
        'cost': mmf_cost
    }
    portfolio.append(mmf_entry)

    # 채권형 남은 현금으로 MMF ETF 추가 매수
    bond_cash = half_invest - (bond_cost + mmf_cost)
    while bond_cash >= mmf_price.close:
        mmf_entry['units'] += 1
        mmf_entry['cost'] += mmf_price.close
        bond_cash -= mmf_price.close

    # 최종 합산
    total_cost = sum(p['cost'] for p in portfolio)
    remain_cash = total_invest - total_cost

    return portfolio, round(total_cost, 2), round(remain_cash, 2), round(delta, 4)
