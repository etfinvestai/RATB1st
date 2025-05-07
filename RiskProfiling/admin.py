from django.contrib import admin
from .models import InvestorSurvey, ETF, ETFPrice
from .models import StrategyRank
from .models import Portfolio, PortfolioItem, PortfolioNAV, PortfolioVersion



@admin.register(InvestorSurvey)
class InvestorSurveyAdmin(admin.ModelAdmin):
    list_display = ('name', 'age', 'score', 'profile_type', 'is_vulnerable')

class ETFPriceInline(admin.TabularInline):
    model = ETFPrice
    extra = 0

@admin.register(ETF)
class ETFAdmin(admin.ModelAdmin):
    list_display = ('name', 'ticker', 'asset_class', 'sub_strategy', 'region', 'inception_date', 'expense_ratio')
    search_fields = ('name', 'ticker')
    list_filter = ('asset_class', 'region')
    inlines = [ETFPriceInline]

@admin.register(ETFPrice)
class ETFPriceAdmin(admin.ModelAdmin):
    list_display = ('etf', 'date', 'close', 'aum')
    list_filter = ('etf', 'date')

@admin.register(StrategyRank)
class StrategyRankAdmin(admin.ModelAdmin):
    list_display = ('year', 'month', 'sub_strategy', 'rank')
    list_filter = ('year', 'month')
    search_fields = ('sub_strategy',)

@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type')
    search_fields = ('name',)
    list_filter = ('type',)


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    list_display = ('version', 'etf', 'quantity')
    search_fields = ('version__portfolio__name', 'etf__ticker')  # ✅ 경로 수정
    list_filter = ('version__portfolio__type',)

@admin.register(PortfolioVersion)
class PortfolioVersionAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'base_date', 'created_at')
    date_hierarchy = 'base_date'
    list_filter = ('portfolio__type',)

@admin.register(PortfolioNAV)
class PortfolioNAVAdmin(admin.ModelAdmin):
    list_display = ('portfolio', 'date', 'nav')
    search_fields = ('portfolio__name',)
    list_filter = ('date',)
    date_hierarchy = 'date'
