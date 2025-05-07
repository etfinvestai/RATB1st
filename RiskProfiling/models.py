from django.db import models



class InvestorSurvey(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    q1_1 = models.FloatField()
    q1_2 = models.FloatField()
    q1_3 = models.FloatField()
    q2_1 = models.FloatField()
    q2_2 = models.FloatField()
    q2_3 = models.FloatField()
    q2_4 = models.FloatField()
    q3 = models.FloatField()
    is_vulnerable = models.BooleanField(default=False)  # ✅ 이 줄 추가!
    score = models.FloatField(null=True, blank=True)
    profile_type = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.age})"

class ETF(models.Model):
    name = models.CharField(max_length=100)
    ticker = models.CharField(max_length=20, unique=True)
    krcode = models.CharField(max_length=30, unique=True)
    asset_class = models.CharField(max_length=50)
    sub_strategy = models.CharField(max_length=100, null=True, blank=True)
    region = models.CharField(max_length=100, null=True, blank=True)
    inception_date = models.DateField(null=True, blank=True)
    expense_ratio = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} ({self.ticker})"

class ETFPrice(models.Model):
    etf = models.ForeignKey(ETF, on_delete=models.CASCADE)
    date = models.DateField()
    close = models.FloatField()
    aum = models.FloatField()

    class Meta:
        unique_together = ('etf', 'date')

    def __str__(self):
        return f"{self.etf.ticker} - {self.date}"

class ETFDelta(models.Model):
    etf = models.ForeignKey(ETF, on_delete=models.CASCADE)
    date = models.DateField()                                       #auto_now_add=True
    delta = models.FloatField()
    base_price = models.FloatField(null=False, default=0.0)

    class Meta:
        unique_together = ('etf', 'date')

    def __str__(self):
        return f"{self.etf.name} - Δ: {self.delta:.4f}"

class SubStrategyRanking(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    sub_strategy = models.CharField(max_length=100)
    rank = models.IntegerField()

    class Meta:
        unique_together = ('year', 'month', 'sub_strategy')
        ordering = ['year', 'month', 'rank']

    def __str__(self):
        return f"{self.year}-{self.month:02d} | {self.sub_strategy} → {self.rank}"

class StrategyRank(models.Model):
    year = models.IntegerField()
    month = models.IntegerField()
    sub_strategy = models.CharField(max_length=100)
    rank = models.IntegerField()

    class Meta:
        unique_together = ('year', 'month', 'sub_strategy')

    def __str__(self):
        return f"{self.year}-{self.month} / {self.sub_strategy}: {self.rank}"

class Portfolio(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)  # 이름별 하나만 유지
    PORTFOLIO_TYPE_CHOICES = [
        ('bond', '채권형'),
        ('equity', '주식형'),
        ('combined', '혼합형'),
    ]
    type = models.CharField(max_length=20, choices=PORTFOLIO_TYPE_CHOICES)

    def __str__(self):
        return self.name


class PortfolioVersion(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='versions')
    base_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('portfolio', 'base_date')

    def __str__(self):
        return f"{self.portfolio.name} @ {self.base_date}"

class PortfolioItem(models.Model):
    version = models.ForeignKey(PortfolioVersion, on_delete=models.CASCADE, related_name='items', null=True)
    etf = models.ForeignKey('ETF', on_delete=models.CASCADE)
    quantity = models.IntegerField()


class PortfolioNAV(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    date = models.DateField()
    nav = models.FloatField()

    class Meta:
        unique_together = ('portfolio', 'date')