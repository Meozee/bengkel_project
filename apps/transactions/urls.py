# apps/transactions/urls.py

from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    path('', views.transaction_list, name='transaction_list'),
    path('create/', views.transaction_create, name='transaction_create'),
    path('edit/<int:pk>/', views.transaction_edit, name='transaction_edit'),
    path('delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),
    
    path('detail/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    
    path('edit/<int:pk>/', views.transaction_edit, name='transaction_edit'),
    # Action Khusus
    path('status/<int:pk>/<str:new_status>/', views.update_status, name='update_status'),
    
    # API Helpers
    path('api/item-price/<int:item_id>/', views.api_get_item_price, name='api_get_item_price'),
    path('api/service-price/<int:service_id>/', views.api_get_service_price, name='api_get_service_price'),
    path('print/<int:pk>/', views.transaction_print, name='transaction_print'),    
]