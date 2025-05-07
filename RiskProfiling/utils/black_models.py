import math
from scipy.stats import norm

def black_model_call_delta(F, K, T, r, sigma):
    """Black Model Delta 계산 (Call Option)"""
    try:
        d1 = (math.log(F / K) + 0.5 * sigma**2 * T) / (sigma * math.sqrt(T))
        delta = math.exp(-r * T) * norm.cdf(d1)
        return delta
    except (ZeroDivisionError, ValueError):
        return None
