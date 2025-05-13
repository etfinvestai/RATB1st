from django import forms
from .models import InvestorSurvey

class InvestorSurveyForm(forms.ModelForm):
    Q1_1_CHOICES = [
        (7.5, "여유자금 투자"),
        (5, "노후 자금 마련"),
        (2.5, "목적자금 마련 (결혼자금, 교육자금 등)"),
        (0, "사용 예정 자금 단기운용"),
    ]

    Q1_2_CHOICES = [
        (12, "기대수익이 높다면 원금 초과 손실도 감수할 수 있다."),
        (9, "기대수익이 높다면 20% 초과 손실도 감수할 수 있다."),
        (6, "원하는 수익이 있다면 20% 이내 손실 감수 가능하다."),
        (3, "일정 수익을 기대한다면 경미한 손실은 감수 가능하다."),
        (-9, "원금 보존이 최우선이다."),
    ]

    Q1_3_CHOICES = [
        (5, "3년 이상"),
        (4, "2년 이상 ~ 3년 미만"),
        (3, "1년 이상 ~ 2년 미만"),
        (2, "6개월 이상 ~ 1년 미만"),
        (1, "6개월 미만"),
    ]

    Q2_1_CHOICES = [
        (5, "현재 수익 안정, 향후 유지/증가 예상"),
        (3, "현재 수익 있으나 향후 감소/불안정 예상"),
        (1, "현재 수익 없음 또는 연금 등이 주수입원"),
    ]

    Q2_2_CHOICES = [
        (5, "국내외주식형 펀드 등 고위험 상품 경험"),
        (4, "인덱스 주식형 펀드 등 경험"),
        (3, "채권형 펀드, 회사채 등 경험"),
        (2, "국공채펀드, ELB/DLB 등"),
        (1, "예적금, MMF 등"),
    ]

    Q2_3_CHOICES = [
        (3, "80% 이상"),
        (2.5, "60% 이상 ~ 80% 미만"),
        (2, "40% 이상 ~ 60% 미만"),
        (1.5, "20% 이상 ~ 40% 미만"),
        (1, "20% 미만"),
        (0, "없음"),
    ]

    Q2_4_CHOICES = [
        (1, "금융상품에 대해 스스로 결정한 적 없음"),
        (2, "예금과 펀드 차이 구별 가능"),
        (3, "설명을 들으면 이해 가능"),
        (4, "설명서 읽고 스스로 이해 가능"),
    ]

    Q3_CHOICES = [
        (2, "20세 미만"),
        (2.5, "20대"),
        (3, "30대"),
        (3, "40대"),
        (2.5, "50대"),
        (2, "60대 이상"),
    ]

    IS_VULNERABLE_CHOICES = [
        (True, "금융 이해 부족 또는 투자 경험 없음"),
        (False, "해당 없음"),
    ]

    q1_1 = forms.ChoiceField(choices=Q1_1_CHOICES, widget=forms.RadioSelect, label="1-1. 투자 목적")
    q1_2 = forms.ChoiceField(choices=Q1_2_CHOICES, widget=forms.RadioSelect, label="1-2. 기대 수익과 손실 감수 성향")
    q1_3 = forms.ChoiceField(choices=Q1_3_CHOICES, widget=forms.RadioSelect, label="1-3. 투자 가능 기간")
    q2_1 = forms.ChoiceField(choices=Q2_1_CHOICES, widget=forms.RadioSelect, label="2-1. 수입원 안정성")
    q2_2 = forms.ChoiceField(choices=Q2_2_CHOICES, widget=forms.RadioSelect, label="2-2. 투자 경험")
    q2_3 = forms.ChoiceField(choices=Q2_3_CHOICES, widget=forms.RadioSelect, label="2-3. 금융자산 내 투자상품 비중")
    q2_4 = forms.ChoiceField(choices=Q2_4_CHOICES, widget=forms.RadioSelect, label="2-4. 금융상품 이해도")
    q3 = forms.ChoiceField(choices=Q3_CHOICES, widget=forms.RadioSelect, label="3. 나이")
    is_vulnerable = forms.ChoiceField(choices=IS_VULNERABLE_CHOICES, widget=forms.RadioSelect, label="4. 금융 취약 소비자 여부")

    class Meta:
        model = InvestorSurvey
        fields = ['name', 'age', 'q1_1', 'q1_2', 'q1_3', 'q2_1', 'q2_2', 'q2_3', 'q2_4', 'q3', 'is_vulnerable']
