from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # List dan CRUD
    path('', views.transaction_list, name='transaction_list'),
    path('create/', views.transaction_create, name='transaction_create'),
    path('edit/<int:pk>/', views.transaction_edit, name='transaction_edit'),
    path('delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),
    
    # API endpoints untuk autocomplete dan autofill
    path('api/search-items/', views.api_search_items, name='api_search_items'),
    path('api/item-price/<int:item_id>/', views.api_get_item_price, name='api_get_item_price'),
    path('api/service-price/<int:service_id>/', views.api_get_service_price, name='api_get_service_price'),
]