"""
URL configuration for bengkel_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

# bengkel_project/urls.py
# bengkel_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views  # <-- 1. IMPORT INI

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Jadikan halaman dashboard sebagai halaman utama
    path('', include('apps.dashboard.urls', namespace='dashboard')),
    
    # Arahkan semua URL yang berawalan 'transactions/' ke apps/transactions/urls.py
    path('transactions/', include('apps.transactions.urls', namespace='transactions')),
    path('inventory/', include('apps.inventory.urls', namespace='inventory')),
    path('purchases/', include('apps.purchases.urls', namespace='purchases')),
    path('master-data/', include('apps.master_data.urls')),
    path('expenses/', include('apps.expenses.urls', namespace='expenses')),
    path('reports/', include('apps.reports.urls')),

    path('login/', auth_views.LoginView.as_view(
        template_name='registration/login.html'
    ), name='login'),

    # Path untuk LOGOUT
    # LogoutView bawaan Django tidak perlu template, ia akan langsung logout
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)