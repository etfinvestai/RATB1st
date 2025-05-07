from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Avg
from django.utils.timezone import make_aware
from .forms import InvestorSurveyForm
from .models import StrategyRank
from .models import InvestorSurvey
from .models import ETF, ETFPrice, ETFDelta, Portfolio, PortfolioNAV, PortfolioItem, PortfolioVersion
from datetime import date, datetime, timedelta
from .utils.black_models import black_model_call_delta
from RiskProfiling.utils.bond_portfolio import generate_bond_portfolio
from .utils.strategy_portfolio import generate_strategy_portfolio
from .utils.combined_portfolio import generate_combined_portfolio
from django.db.models import Q
from RiskProfiling.utils.nav_utils import calculate_nav_range


import json
import os
import csv
import io
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Algorithm.settings")
django.setup()



def investor_survey_view(request):
    if request.method == 'POST':
        form = InvestorSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.score = calculate_score(survey)
            survey.profile_type = classify_profile(survey)
            survey.save()
            return redirect('survey_result', pk=survey.pk)
    else:
        form = InvestorSurveyForm()
    return render(request, 'RiskProfiling/form.html', {'form': form})

def calculate_score(survey):
    try:
        return (
            float(survey.q1_1) +
            float(survey.q1_2) +
            float(survey.q1_3) +
            float(survey.q2_1) +
            float(survey.q2_2) +
            float(survey.q2_3) +
            float(survey.q2_4) +
            float(survey.q3)
        )
    except (ValueError, TypeError):
        return 0

def classify_profile(survey):
    if survey.is_vulnerable == 'True' or survey.is_vulnerable is True:
        return '안정형'
    
    score = survey.score
    if score > 35:
        return '공격투자형'
    elif score > 30:
        return '적극투자형'
    elif score > 25:
        return '위험중립형'
    elif score > 20:
        return '안정추구형'
    else:
        return '안정형'

def survey_result_view(request, pk):
    survey = InvestorSurvey.objects.get(pk=pk)
    return render(request, 'RiskProfiling/result.html', {'survey': survey})

def portfolio_recommend_view(request, investor_id):
    investor = get_object_or_404(InvestorSurvey, pk=investor_id)
    profile = investor.profile_type
    today = date.today()

    if profile in ['안정형', '안정추구형']:
        etfs = ETF.objects.filter(asset_class__icontains='bond')
    elif profile in ['적극투자형', '위험중립형']:
        etfs = ETF.objects.filter(asset_class__in=['bond', 'stock'])  # 주식/채권
    elif profile == '공격투자형':
        etfs = ETF.objects.filter(asset_class__icontains='stock')
    else:
        etfs = ETF.objects.none()

    deltas = ETFDelta.objects.filter(etf__in=etfs, date=today)
    total = sum(d.delta for d in deltas)

    portfolio = [
        {
            'name': d.etf.name,
            'ticker': d.etf.ticker,
            'asset_class': d.etf.asset_class,
            'delta': round(d.delta, 4),
            'weight': round((d.delta / total) * 100, 2) if total else 0
        }
        for d in deltas
    ]

    return render(request, 'RiskProfiling/portfolio_result.html', {
        'investor': investor,
        'portfolio': portfolio
    })

def etf_deltas_view(request):
    etf_name = "KIWOOM 국고채10년"
    etf = ETF.objects.filter(name=etf_name).first()
    context = {'etf': etf, 'etf_name': etf_name}

    if request.method == 'POST' and etf:
        try:
            # 👉 폼 입력값 받기
            r = float(request.POST.get('rate')) / 100  # 퍼센트 입력 시 0.01 곱하기
            sigma = float(request.POST.get('sigma')) / 100
            base_date = datetime.strptime(request.POST.get('base_date'), "%Y-%m-%d").date()
            today = datetime.strptime(request.POST.get('today'), "%Y-%m-%d").date()
            AUM = int(request.POST.get('aum').replace(',', ''))
            K = float(request.POST.get('K').replace(',', ''))

            # 👉 포트폴리오 생성 함수 호출
            result = generate_bond_portfolio(etf, base_date, today, r, sigma, AUM, K)

            # 👉 context에 결과 추가
            context.update(result)
            context.update({
                'r': r * 100,  # 다시 %로 보여주기
                'sigma': sigma * 100,
                'base_date': base_date,
                'today': today,
                'aum': AUM,
                'K': K,
                'success': True,
            })

        except Exception as e:
            context['error'] = f"❌ 오류: {e}"

    return render(request, 'RiskProfiling/etf_deltas.html', context)

def upload_strategy_rank_view(request):
    if request.method == 'POST' and request.FILES.get('file'):
        csv_file = request.FILES['file']
        decoded_file = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded_file))

        count = 0
        for row in reader:
            try:
                # ✅ 키 정리
                #row = {k.strip().lower(): v.strip() for k, v in row.items()}
                row = {k.strip().lower().lstrip('\ufeff'): v.strip() for k, v in row.items()}

                year = int(row['year'])
                month = int(row['month'])
                sub_strategy = row['sub_strategy']
                rank = int(row['rank'])

                StrategyRank.objects.update_or_create(
                    year=year,
                    month=month,
                    sub_strategy=sub_strategy,
                    defaults={'rank': rank}
                )
                count += 1
            except Exception as e:
                print(f"❌ 해당 행을 처리하는 데 오류가 발생했습니다: {e}")
                continue

        return render(request, 'RiskProfiling/upload_result.html', {'count': count})

    return render(request, 'RiskProfiling/upload_strategy_rank.html')

# ✅ final views.py > strategy_portfolio_view
def strategy_portfolio_view(request):
    context = {}

    if request.method == 'POST':
        try:
            base_date_str = request.POST.get("base_date")
            total_invest_str = request.POST.get("total_invest")

            if not base_date_str or not total_invest_str:
                raise ValueError("기준일 또는 투자금액이 입력되지 않았습니다.")

            base_date = datetime.strptime(base_date_str, "%Y-%m-%d").date()
            total_invest = int(total_invest_str.replace(',', ''))

            context['base_date'] = base_date
            context['total_invest'] = total_invest

            # 변경: 수량 포함된 주식형 포트폴리오 반환
            portfolio = generate_strategy_portfolio(base_date, total_invest)

            # 🔁 현금이 1만원 이하가 될 때까지 순위 높은 ETF부터 한 주씩 추가 매수
            total_cost = sum(p['cost'] for p in portfolio)
            remain_cash = total_invest - total_cost
            i = 0
            while remain_cash > 10000 and i < len(portfolio):
                item = portfolio[i]
                if remain_cash >= item['price']:
                    item['units'] += 1
                    item['cost'] += item['price']
                    remain_cash -= item['price']
                i = (i + 1) % len(portfolio)

            context['portfolio'] = portfolio
            context['remain_cash'] = round(remain_cash, 2)
            context['success'] = True

        except Exception as e:
            context['error'] = f"\u274c 오류 발생: {e}"

    return render(request, 'RiskProfiling/strategy_portfolio.html', context)




def combined_portfolio_view(request):
    context = {}
    if request.method == 'POST':
        try:
            base_date_str = request.POST.get('base_date')
            delta_date_str = request.POST.get('today')  # 델타 계산일 = 현재일
            total_invest_str = request.POST.get('total_invest')
            rate_str = request.POST.get('rate')
            sigma_str = request.POST.get('sigma')
            K_str = request.POST.get('K')

            # 입력값 유효성 검사
            if not (base_date_str and delta_date_str and total_invest_str and rate_str and sigma_str):
                raise ValueError("모든 필드를 입력해 주세요.")

            # 파라미터 변환
            r = float(rate_str) / 100
            sigma = float(sigma_str) / 100
            total_invest = int(total_invest_str.replace(',', ''))
            K = float(K_str.replace(',', '')) if K_str else None

            # 포트폴리오 생성
            from .utils.combined_portfolio import generate_combined_portfolio
            portfolio, total_cost, remain_cash, delta = generate_combined_portfolio(
                base_date_str, total_invest, delta_date_str, r, sigma, K
            )

            # 결과 context 전달
            context.update({
                'portfolio': portfolio,
                'total_cost': total_cost,
                'remain_cash': remain_cash,
                'delta': delta,
                'base_date': base_date_str,
                'total_invest': total_invest,
                'r': r * 100,
                'sigma': sigma * 100,
                'K': K,
                'today': delta_date_str,
                'success': True,
            })

        except Exception as e:
            context['error'] = f"❌ 오류 발생: {str(e)}"

    return render(request, 'RiskProfiling/combined_portfolio.html', context)


def upload_etf_price_view(request):
    context = {}
    if request.method == 'POST' and 'price_file' in request.FILES:
        csv_file = request.FILES['price_file']
        decoded = csv_file.read().decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        count = 0

        for row in reader:
            try:
                row = {k.strip().lower().lstrip('\ufeff'): v.strip() for k, v in row.items()}
                etf = ETF.objects.get(ticker=row['krx_code'])
                date = datetime.strptime(row['date'], '%Y-%m-%d').date()
                price = float(row['close'])
                aum = float(row.get('aum', 0))

                ETFPrice.objects.update_or_create(
                    etf=etf,
                    date=date,
                    defaults={'close': price, 'aum': aum}
                )
                count += 1
            except Exception as e:
                print(f"❌ Error row: {e}")
                continue

        context['success'] = True
        context['uploaded_count'] = count

    return render(request, 'RiskProfiling/upload_etf_price.html', context)


def manual_portfolio_upload_view(request):
    context = {}
    if request.method == 'POST':
        try:
            name = request.POST.get('portfolio_name')
            type_ = request.POST.get('portfolio_type')
            base_date = request.POST.get('base_date')
            etf_data = request.POST.get('etf_data')

            if not (name and type_ and base_date and etf_data):
                raise ValueError("모든 항목을 입력해주세요.")

            base_date_obj = datetime.strptime(base_date, "%Y-%m-%d").date()

            # 포트폴리오 생성
            portfolio = Portfolio.objects.create(
                name=name,
                type=type_,
                base_date=base_date_obj,
                initial_invest=0,  # 계산 후 반영
                cash=0
            )

            total_value = 0
            lines = etf_data.strip().splitlines()
            for line in lines:
                try:
                    ticker, quantity = line.strip().split(',')
                    etf = ETF.objects.get(ticker=ticker.strip())
                    quantity = int(quantity.strip())
                    price_obj = ETFPrice.objects.filter(etf=etf, date=base_date_obj).first()
                    if not price_obj:
                        raise ValueError(f"{etf.name}의 {base_date} 기준 주가가 없습니다.")

                    cost = price_obj.close * quantity
                    total_value += cost

                    PortfolioItem.objects.create(
                        portfolio=portfolio,
                        etf=etf,
                        quantity=quantity
                    )
                except Exception as item_error:
                    raise ValueError(f"입력 오류 또는 주가 누락: {line} ({item_error})")

            # NAV 저장
            PortfolioNAV.objects.update_or_create(
                portfolio=portfolio,
                date=base_date_obj,
                defaults={'nav': total_value}
            )

            # 포트폴리오 초기값 업데이트
            portfolio.initial_invest = total_value
            portfolio.save()

            context['success'] = True
            context['portfolio_name'] = name
            context['date'] = base_date
            context['nav'] = round(total_value, 2)

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'RiskProfiling/upload_portfolio.html', context)

def calculate_portfolio_nav_view(request):
    if request.method == 'POST':
        date_str = request.POST.get('nav_date')
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return render(request, 'RiskProfiling/calculate_nav.html', {'error': '날짜 형식 오류'})

        portfolio_names = Portfolio.objects.values_list('name', flat=True).distinct()
        updated = 0

        for name in portfolio_names:
            # 🔍 해당일자 기준 최신 포트폴리오 가져오기
            latest_portfolio = Portfolio.objects.filter(
                name=name,
                base_date__lte=target_date
            ).order_by('-base_date').first()

            if not latest_portfolio:
                continue  # 등록된 구성이 없는 경우 skip

            # NAV 계산
            total = 0
            for item in latest_portfolio.items.all():
                price_obj = ETFPrice.objects.filter(etf=item.etf, date=target_date).first()
                if price_obj:
                    total += item.quantity * price_obj.close
            total += latest_portfolio.cash

            # 저장
            PortfolioNAV.objects.update_or_create(
                portfolio=latest_portfolio,
                date=target_date,
                defaults={'nav': total}
            )
            updated += 1

        return render(request, 'RiskProfiling/calculate_nav.html', {
            'success': True,
            'updated_count': updated,
            'date': date_str
        })

    return render(request, 'RiskProfiling/calculate_nav.html')

def upload_portfolio_csv_view(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('portfolio_file'):
        try:
            csv_file = request.FILES['portfolio_file']
            decoded = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded))

            portfolios = {}
            for row in reader:
                row = {k.strip().lower().lstrip('\ufeff'): v.strip() for k, v in row.items()}
                key = (row['portfolio_name'], row['portfolio_type'], row['base_date'])
                if key not in portfolios:
                    portfolios[key] = []
                portfolios[key].append((row['ticker'], int(row['quantity'])))

            created_count = 0
            for (name, type_, base_date), items in portfolios.items():
                date_obj = datetime.strptime(base_date, '%Y-%m-%d').date()

                # 1. get or create Portfolio
                portfolio, _ = Portfolio.objects.get_or_create(
                    name=name,
                    defaults={'type': type_}
                )

                # 2. create PortfolioVersion
                version, created = PortfolioVersion.objects.get_or_create(
                    portfolio=portfolio,
                    base_date=date_obj
                )

                if not created:
                    version.items.all().delete()  # 덮어쓰기

                for ticker, quantity in items:
                    if ticker.upper() == 'CASH':
                        version.portfolio.cash = quantity
                        version.portfolio.save()
                        continue  # 현금 처리하고 ETF 생략
                    
                    etf = ETF.objects.filter(ticker=ticker).first()
                    if not etf:
                        raise ValueError(f"ETF {ticker} 가 존재하지 않습니다.")

                    PortfolioItem.objects.create(
                        version=version,
                        etf=etf,
                        quantity=quantity
                    )

                created_count += 1

            context['success'] = True
            context['created'] = created_count

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'RiskProfiling/upload_portfolio_csv.html', context)


def portfolio_nav_chart_view(request, portfolio_id):
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)
    navs = PortfolioNAV.objects.filter(portfolio=portfolio).order_by('date')

    dates = [nav.date.strftime("%Y-%m-%d") for nav in navs]
    values = [nav.nav for nav in navs]

    return render(request, 'RiskProfiling/portfolio_nav_chart.html', {
        'portfolio': portfolio,
        'dates': dates,
        'values': values,
    })

def get_portfolio_on_date(name: str, target_date: date):
    return Portfolio.objects.filter(
        name=name,
        base_date__lte=target_date
    ).order_by('-base_date').first()

def calculate_nav_view(request):
    context = {}

    if request.method == 'POST':
        try:
            start_date_str = request.POST.get("start_date")
            end_date_str = request.POST.get("end_date")

            if not start_date_str or not end_date_str:
                raise ValueError("시작일과 종료일을 모두 입력해야 합니다.")

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            results = calculate_nav_range(start_date, end_date)
            context['results'] = results
            context['success'] = True

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'RiskProfiling/calculate_nav.html', context)

def calculate_nav_view(request):
    context = {}

    if request.method == 'POST':
        try:
            start_date_str = request.POST.get("start_date")
            end_date_str = request.POST.get("end_date")

            if not start_date_str or not end_date_str:
                raise ValueError("시작일과 종료일을 모두 입력해야 합니다.")

            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            results = calculate_nav_range(start_date, end_date)
            context['results'] = results
            context['success'] = True

        except Exception as e:
            context['error'] = str(e)

    return render(request, 'RiskProfiling/calculate_nav.html', context)

