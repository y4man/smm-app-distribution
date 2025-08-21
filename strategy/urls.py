from django.urls import path
from . import views

urlpatterns = [
    

    # path('strategies/', views.StrategyListCreateView.as_view(), name='strategy_list_create'),

    # ✅
    path('client/<int:client_id>/strategy', views.StrategyListCreateView.as_view(), name='strategy_list_create'),
]