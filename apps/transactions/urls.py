# apps/transactions/urls.py

from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),
    path('new/', views.transaction_create_or_update_view, name='transaction_create'),
    path('<int:pk>/edit/', views.transaction_create_or_update_view, name='transaction_update'),

    # URL untuk autocomplete (AJAX)
    path('item-autocomplete/', views.item_autocomplete, name='item_autocomplete'),
    # ✅ TAMBAHKAN URL INI
    path('service-autocomplete/', views.service_autocomplete, name='service_autocomplete'),
]