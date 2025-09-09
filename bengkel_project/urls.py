# bengkel_project/urls.py - VERSI BENAR
from django.contrib import admin
from django.urls import path, include
# V Impor view login dan logout dari aplikasi users V
from users.views import login_view, logout_view

urlpatterns = [
    path('admin/', admin.site.urls),

    # URL Autentikasi
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('users/', include('users.urls', namespace='users')),
    path('transactions/', include('transactions.urls')),
    path('inventory/', include('inventory.urls', namespace='inventory')), # <-- TAMBAHKAN INI
    path('', include('analytics.urls')),
]