# strategy_portfolio.py

from RiskProfiling.models import ETF, ETFPrice, StrategyRank
from .rsi import calculate_rsi


def generate_strategy_portfolio(base_date, total_invest=None):
    year = base_date.year
    month = base_date.month
    target_date = base_date

    ranks = StrategyRank.objects.filter(year=year, month=month).order_by('rank')
    rsi_cache = {}
    etf_candidates = []

    for strategy in ranks:
        sub = strategy.sub_strategy
        etfs = ETF.objects.filter(sub_strategy=sub)

        etf_rsi_list = []
        for etf in etfs:
            if (etf.id, base_date) in rsi_cache:
                rsi = rsi_cache[(etf.id, base_date)]
            else:
                rsi = calculate_rsi(etf, base_date)
                rsi_cache[(etf.id, base_date)] = rsi
            if rsi is not None:
                etf_rsi_list.append((etf, rsi))

        sorted_etfs = sorted(etf_rsi_list, key=lambda x: x[1])[:2]

        for etf, rsi in sorted_etfs:
            price = ETFPrice.objects.filter(etf=etf, date=target_date).first()
            if price:
                etf_candidates.append({
                    'name': etf.name,
                    'ticker': etf.ticker,
                    'sub_strategy': sub,
                    'rsi': rsi,
                    'price': price.close
                })

        if len(etf_candidates) >= 10:
            break

    selected_etfs = etf_candidates[:10]
    if total_invest is not None:
        n = len(selected_etfs)
        weight = total_invest / n if n else 0
        for item in selected_etfs:
            units = int(weight / item['price']) if item['price'] > 0 else 0
            cost = units * item['price']
            item.update({'units': units, 'cost': cost})

    return selected_etfs
