import os
import sys
import django
from datetime import datetime

# Django 설정 초기화
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', '..'))
sys.path.append(PROJECT_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Algorithm.settings')
django.setup()

from RiskProfiling.models import ETF, ETFPrice
from RiskProfiling.utils.black_model import black_model_call_delta

# 사용자 입력
try:
    aum = float(input("💰 총 AUM (예: 1000000000): ").strip())
    base_date = datetime.strptime(input("📅 기준일 (예: 2024-07-01): ").strip(), "%Y-%m-%d").date()
    today = datetime.strptime(input("📅 계산일 (예: 2024-12-30): ").strip(), "%Y-%m-%d").date()
    r = float(input("📈 무위험이자율 r (예: 0.03): ").strip())
    sigma = float(input("📉 변동성 σ (예: 0.2): ").strip())
    K = float(input("🎯 기준가격 K (strike price): ").strip())
except Exception as e:
    print(f"❌ 입력 오류: {e}")
    sys.exit()

# 만기 계산
T = ((today - base_date).days + 0.0001) / 365

# 대상 ETF
etf = ETF.objects.filter(name="KIWOOM 국고채10년").first()
if not etf:
    print("❌ ETF 'KIWOOM 국고채10년'을 찾을 수 없습니다.")
    sys.exit()

# 현재 가격
current_price = ETFPrice.objects.filter(etf=etf, date=today).first()
if not current_price:
    print("❌ 오늘 기준 가격을 찾을 수 없습니다.")
    sys.exit()

F = current_price.close
delta = black_model_call_delta(F, K, T, r, sigma)
print(f"\n✅ Δ 계산 결과: {delta:.4f} (F={F}, K={K}, T={T:.4f}, r={r}, σ={sigma})")

# 포트폴리오 구성
portfolio = []
used_cash = 0
max_weight = 0.25
n_lt = int(delta / max_weight)
remain_weight = delta - (n_lt * max_weight)

# 장기 ETF 선택
lt_etfs = ETF.objects.filter(sub_strategy='10Y').order_by('expense_ratio')[:n_lt + 1]
for i, bond_etf in enumerate(lt_etfs):
    price = ETFPrice.objects.filter(etf=bond_etf, date=today).first()
    if not price:
        continue
    weight = max_weight if i < n_lt else remain_weight
    weight = min(weight, max_weight)
    units = int((aum * weight) / price.close)
    cost = units * price.close
    if units <= 0:
        continue
    portfolio.append({
        'name': bond_etf.name,
        'ticker': bond_etf.ticker,
        'price': price.close,
        'units': units,
        'cost': cost,
        'type': '장기'
    })
    used_cash += cost

# 단기 ETF 구성
remain_cash = aum - used_cash
st_etfs = ETF.objects.filter(sub_strategy='ShortTerm').order_by('expense_ratio')
for st_etf in st_etfs:
    if remain_cash < 10000:
        break
    price = ETFPrice.objects.filter(etf=st_etf, date=today).first()
    if not price:
        continue
    max_st_units = int((aum * max_weight) // price.close)
    units = min(int(remain_cash // price.close), max_st_units)
    cost = units * price.close
    if units <= 0:
        continue
    portfolio.append({
        'name': st_etf.name,
        'ticker': st_etf.ticker,
        'price': price.close,
        'units': units,
        'cost': cost,
        'type': '단기'
    })
    used_cash += cost
    remain_cash -= cost

# 출력
print("\n📊 포트폴리오 구성:")
for p in portfolio:
    print(f"✅ [{p['type']}] {p['name']} ({p['ticker']}) | 단가: {p['price']:.2f} | 수량: {p['units']} | 금액: {p['cost']:.0f} 원")

print(f"\n💰 총 사용금액: {used_cash:,.0f} 원")
print(f"💸 잔여금액: {aum - used_cash:,.0f} 원")
