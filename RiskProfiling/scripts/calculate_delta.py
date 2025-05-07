import os
import sys
import django
import json
from datetime import datetime, date

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Algorithm.settings')
django.setup()

from RiskProfiling.models import ETF, ETFDelta, ETFPrice
from RiskProfiling.utils.black_models import black_model_call_delta

# ✅ 입력파일 로드
config_path = os.path.join(BASE_DIR, 'RiskProfiling/scripts/delta_input.json')

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        params = json.load(f)
except Exception as e:
    print(f"❌ 입력 파일을 불러오지 못했습니다: {e}")
    sys.exit()

try:
    etf_name = params["etf_name"]
    base_date = datetime.strptime(params["base_date"], "%Y-%m-%d").date()
    today = datetime.strptime(params["today"], "%Y-%m-%d").date()
    r = float(params["r"])
    sigma = float(params["sigma"])
    K = float(params["K"])  # 기준가격
except Exception as e:
    print(f"❌ 입력 파싱 실패: {e}")
    sys.exit()

# ETF 및 가격 확인
etf = ETF.objects.filter(name=etf_name).first()
if not etf:
    print(f"❌ '{etf_name}' ETF를 찾을 수 없습니다.")
    sys.exit()

current_price = ETFPrice.objects.filter(etf=etf, date=today).first()
if not current_price:
    print(f"❌ 오늘 날짜({today})의 가격 정보가 없습니다.")
    sys.exit()

F = current_price.close
T = ((today - base_date).days + 0.0001) / 365

# Δ 계산
delta = black_model_call_delta(F, K, T, r, sigma)
ETFDelta.objects.update_or_create(
    etf=etf,
    date=today,
    defaults={'base_price': K, 'delta': delta}
)

print(f"✅ Δ 계산 완료: {etf_name}")
print(f" - K: {K}, F: {F}, r: {r}, σ: {sigma}, T: {T:.4f}")
print(f" - Δ: {delta:.4f}")
