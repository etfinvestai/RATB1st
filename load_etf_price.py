import os
import sys
import csv
from datetime import datetime

# ✅ Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Algorithm.settings')  # 수정
import django
django.setup()

from RiskProfiling.models import ETF, ETFPrice

# ✅ CSV 경로
file_path = 'etf_prices.csv'

# ✅ 파서
def parse_float(value):
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None

def parse_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

# ✅ 저장 처리
success, fail = 0, 0

try:
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for i, row in enumerate(reader):
            # 컬럼 키 정리
            row = {k.strip().lstrip('\ufeff').lower(): v.strip() for k, v in row.items()}

            ticker = row.get('krx_code')
            date = parse_date(row.get('date'))
            close = parse_float(row.get('close'))
            aum = parse_float(row.get('aum'))

            if not ticker or not date:
                print(f"⚠️ ticker 또는 date 없음 → 건너뜀")
                fail += 1
                continue

            try:
                etf = ETF.objects.get(ticker=ticker)
            except ETF.DoesNotExist:
                print(f"❌ ETF '{ticker}' not found in DB. → 건너뜀")
                fail += 1
                continue

            try:
                ETFPrice.objects.update_or_create(
                    etf=etf,
                    date=date,
                    defaults={'close': close, 'aum': aum}
                )
                success += 1
            except Exception as e:
                print(f"❌ 저장 실패: {ticker} @ {date} → {e}")
                fail += 1

except FileNotFoundError:
    print(f"❌ CSV 파일이 없습니다: {file_path}")
    sys.exit()

# ✅ 결과 출력
print(f"\n✅ 가격 저장 완료: {success}건 성공 / {fail}건 실패")
