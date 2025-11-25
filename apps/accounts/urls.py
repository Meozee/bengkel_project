# apps/accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

# TAMBAHKAN BARIS INI
app_name = 'accounts' 

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logs/', views.activity_log_view, name='activity_log'),
]