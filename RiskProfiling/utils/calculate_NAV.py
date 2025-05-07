from .models import PortfolioNAV, ETFPrice
from .utils.nav_utils import get_portfolio_on_date
from .utils.date_utils import daterange  # 또는 business_daterange

def calculate_portfolio_navs_over_period(start_date, end_date):
    portfolio_names = Portfolio.objects.values_list('name', flat=True).distinct()

    for single_date in daterange(start_date, end_date):
        for name in portfolio_names:
            portfolio = get_portfolio_on_date(name, single_date)
            if not portfolio:
                continue  # 이 날짜 이전에도 포트폴리오 없음

            total_value = portfolio.cash
            for item in portfolio.items.all():
                price = ETFPrice.objects.filter(etf=item.etf, date=single_date).first()
                if price:
                    total_value += item.quantity * price.close

            PortfolioNAV.objects.update_or_create(
                portfolio=portfolio,
                date=single_date,
                defaults={'nav': total_value}
            )
