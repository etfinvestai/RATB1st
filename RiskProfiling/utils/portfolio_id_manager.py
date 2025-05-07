from RiskProfiling.models import Portfolio

class PortfolioIDManager:
    @staticmethod
    def get_used_ids():
        return list(Portfolio.objects.values_list('id', flat=True).order_by('id'))

    @staticmethod
    def get_next_available_id(start_from=1):
        used = set(PortfolioIDManager.get_used_ids())
        candidate = start_from
        while candidate in used:
            candidate += 1
        return candidate

    @staticmethod
    def assign_id_if_missing(name, type_, base_date, initial_invest=0, cash=0):
        # 존재하면 반환
        if Portfolio.objects.filter(name=name).exists():
            return Portfolio.objects.get(name=name)

        next_id = PortfolioIDManager.get_next_available_id()
        portfolio = Portfolio.objects.create(
            id=next_id,
            name=name,
            type=type_,
            base_date=base_date,
            initial_invest=initial_invest,
            cash=cash
        )
        return portfolio
