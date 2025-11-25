"""
URL configuration for bengkel_project project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # 1. Django Admin
    path('admin/', admin.site.urls),

    # 2. ACCOUNTS (Login, Logout, Logs)
    # Ini yang memperbaiki error 'namespace not registered'.
    # Semua URL di dalam apps/accounts/urls.py akan diawali dengan 'accounts/'
    # Contoh: localhost:8000/accounts/login/
    # Contoh: localhost:8000/accounts/logs/
    path('accounts/', include('apps.accounts.urls')), 

    # 3. DASHBOARD (Halaman Utama)
    # Kita taruh di root '' agar saat buka localhost:8000 langsung ke dashboard
    path('', include('apps.dashboard.urls')),

    # 4. APPS LAINNYA
    path('transactions/', include('apps.transactions.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('purchases/', include('apps.purchases.urls')),
    path('master-data/', include('apps.master_data.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('reports/', include('apps.reports.urls')),

    # 5. Debug Toolbar (Hanya aktif jika DEBUG=True)
    path("__debug__/", include("debug_toolbar.urls")),
]

# Konfigurasi untuk file statis/media saat development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)