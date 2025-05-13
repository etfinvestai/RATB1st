from django.urls import path
from . import views
from .views import investor_survey_view, survey_result_view, portfolio_recommend_view
from .views import upload_strategy_rank_view, strategy_portfolio_view
from .views import portfolio_nav_chart_view

#from .views import theme_portfolio_view


urlpatterns = [
    path('', views.investor_survey_view, name='investor_survey'),  # 기본 설문
    path('result/<int:pk>/', views.survey_result_view, name='survey_result'),  # 설문 결과
    path('strategy-selection/<int:investor_id>/', views.strategy_selection, name='strategy_selection'),
    
    path('recommend/<int:investor_id>/', views.portfolio_recommend_view, name='portfolio_recommend'),  # 포트폴리오 추천
    path('deltas/', views.etf_deltas_view, name='etf_deltas'),  # 🔥 ETF Delta 목록 보기 추가
    path('upload_strategy_rank/', upload_strategy_rank_view, name='upload_strategy_rank'),
    path('strategy_portfolio/', strategy_portfolio_view, name='strategy_portfolio'),
    path('combined_portfolio/', views.combined_portfolio_view, name='combined_portfolio'),
    path('upload_price/', views.upload_etf_price_view, name='upload_etf_price'),
    path('calculate_nav/', views.calculate_portfolio_nav_view, name='calculate_nav'),
    path('upload_manual_portfolio/', views.manual_portfolio_upload_view, name='upload_manual_portfolio'),
    path('upload_portfolio_csv/', views.upload_portfolio_csv_view, name='upload_portfolio_csv'),
    path('portfolio/<int:portfolio_id>/nav_chart/', portfolio_nav_chart_view, name='portfolio_nav_chart'),

    #path('theme_portfolio/', theme_portfolio_view, name='theme_portfolio'),


]
