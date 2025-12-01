# apps/purchases/urls.py

from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseOrderListView.as_view(), name='purchase_list'),
    path('new/', views.purchase_form_view, name='purchase_create'),
    
    # URL BARU
    path('detail/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('status/<int:pk>/<str:new_status>/', views.update_status, name='update_status'),
    
    path('<int:pk>/edit/', views.purchase_form_view, name='purchase_update'),
    path('<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='purchase_delete'),
    path('api/item-autocomplete/', views.item_autocomplete_view, name='item_autocomplete'),
]