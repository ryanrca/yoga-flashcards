from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('dailycard/', views.daily_card, name='daily_card'),
]
