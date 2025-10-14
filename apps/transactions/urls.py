# apps/transactions/urls.py

from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list_view, name='transaction_list'),
    
    # URL untuk form tambah transaksi (tanpa pk)
    path('new/', views.transaction_create_or_update_view, name='transaction_create'),
    
    # URL untuk form edit transaksi (dengan pk)
    path('<int:pk>/edit/', views.transaction_create_or_update_view, name='transaction_update'),

    path('item-autocomplete/', views.item_autocomplete, name='item_autocomplete'),

]