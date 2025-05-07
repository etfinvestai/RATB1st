# RiskProfiling/utils/rsi.py
from RiskProfiling.models import ETFPrice
from datetime import timedelta

def calculate_rsi(etf, base_date, period=14):
    prices = (
        ETFPrice.objects.filter(etf=etf, date__lte=base_date)
        .order_by('-date')
        .values_list('close', flat=True)[:period + 1]
    )

    if len(prices) < period + 1:
        return None

    gains = []
    losses = []

    for i in range(period):
        delta = prices[i] - prices[i + 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(-delta)

    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 0

    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)
