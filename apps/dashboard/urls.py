# apps/dashboard/urls.py
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Ini akan cocok dengan {% url 'dashboard:dashboard' %} di sidebar-mu
    path('', views.dashboard_view, name='dashboard'),
    
    # Ini untuk mencocokkan LOGIN_REDIRECT_URL = 'dashboard:index' di settings.py
    path('index/', views.dashboard_view, name='index'), 
]