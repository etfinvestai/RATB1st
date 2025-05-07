import os
import sys
import csv
from datetime import datetime

# ✅ Django 설정
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Algorithm.settings')  # ⚠️ settings 경로에 맞게 수정
import django
django.setup()

from RiskProfiling.models import ETF

# ✅ CSV 파일 경로
file_path = 'etf_universe.csv'  # 실제 파일 이름

# ✅ 파서 함수
def parse_date(value):
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def parse_float(value):
    try:
        return float(value.replace(",", "").strip())
    except (ValueError, AttributeError):
        return None

# ✅ 저장 처리
success, fail = 0, 0

try:
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            row = {k.strip().lstrip('\ufeff'): v.strip() for k, v in row.items()}

            name = row.get('Local_short_NAME')
            ticker = row.get('KRX_code')
            krcode = row.get('isin_code')
            asset = row.get('Asset')
            sub_strategy = row.get('sub_strategy')
            region = row.get('region')
            inception = parse_date(row.get('inception'))
            ter = parse_float(row.get('TER'))

            if not name or not ticker:
                print(f"❌ 누락된 값 - name: {name}, ticker: {ticker}")
                fail += 1
                continue

            try:
                ETF.objects.update_or_create(
                    ticker=ticker,
                    defaults={
                        'name': name,
                        'krcode': krcode,
                        'asset_class': asset,
                        'sub_strategy': sub_strategy,
                        'region': region,
                        'inception_date': inception,
                        'expense_ratio': ter,
                    }
                )
                success += 1
            except Exception as e:
                print(f"❌ 저장 실패: {name} ({ticker}) → {e}")
                fail += 1

except FileNotFoundError:
    print(f"❌ CSV 파일이 없습니다: {file_path}")
    sys.exit()

print(f"\n✅ ETF 저장 완료: {success}건 성공 / {fail}건 실패")
