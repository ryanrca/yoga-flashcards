from django.urls import path
from .views import login_view, logout_view, auth_status

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('auth-status/', auth_status, name='auth_status'),
]
