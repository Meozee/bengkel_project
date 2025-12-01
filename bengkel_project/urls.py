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

    # 2. ACCOUNTS
    path('accounts/', include('apps.accounts.urls')),

    # 3. DASHBOARD
    path('', include('apps.dashboard.urls')),

    # 4. APPS LAINNYA
    path('transactions/', include('apps.transactions.urls')),
    path('inventory/', include('apps.inventory.urls')),
    path('purchases/', include('apps.purchases.urls')),
    path('master-data/', include('apps.master_data.urls')),
    path('expenses/', include('apps.expenses.urls')),
    path('reports/', include('apps.reports.urls')),

    # 5. Debug Toolbar
    path("__debug__/", include("debug_toolbar.urls")),
]

if settings.DEBUG:
    # MEDIA OK
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # STATIC — hanya gunakan STATICFILES_DIRS (bukan STATIC_ROOT!)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
