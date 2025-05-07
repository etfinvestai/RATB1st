from datetime import date
from RiskProfiling.models import Portfolio, PortfolioVersion, PortfolioNAV, ETFPrice
from .date_utils import daterange

def get_portfolio_version_on(portfolio_name: str, target_date: date):
    return PortfolioVersion.objects.filter(
        portfolio__name=portfolio_name,
        base_date__lte=target_date
    ).order_by('-base_date').first()

def calculate_nav_range(start_date, end_date):
    portfolio_names = Portfolio.objects.values_list('name', flat=True).distinct()
    results = []

    for d in daterange(start_date, end_date):
        for name in portfolio_names:
            version = get_portfolio_version_on(name, d)
            if not version:
                continue  # 구성 없음 → 계산 불가

            total = 0
            for item in version.items.all():
                price = ETFPrice.objects.filter(etf=item.etf, date=d).first()
                if price:
                    total += item.quantity * price.close

            PortfolioNAV.objects.update_or_create(
                portfolio=version.portfolio,
                date=d,
                defaults={'nav': total}
            )
            results.append((name, d.strftime("%Y-%m-%d"), round(total, 2)))

    return results
