# apps/accounts/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts' 

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logs/', views.activity_log_view, name='activity_log'),
    
    # --- TAMBAHKAN BARIS INI ---
    # Ini supaya saat buka link ini, dia masuk ke views.change_password_view (yang ada log-nya)
    path('change-password/', views.change_password_view, name='change_password'),
]