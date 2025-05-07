from datetime import timedelta

def daterange(start_date, end_date):
    """
    start_date부터 end_date까지 모든 날짜를 하루 단위로 생성합니다.
    """
    for n in range((end_date - start_date).days + 1):
        yield start_date + timedelta(n)


def business_daterange(start_date, end_date, business_days):
    """
    business_days (set of date) 기준으로 비즈니스 데이만 생성합니다.
    """
    for current_date in daterange(start_date, end_date):
        if current_date in business_days:
            yield current_date
