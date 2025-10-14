from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('', views.PurchaseOrderListView.as_view(), name='purchase_list'),
    path('new/', views.purchase_form_view, name='purchase_create'),
    path('<int:pk>/edit/', views.purchase_form_view, name='purchase_update'),
    path('<int:pk>/delete/', views.PurchaseOrderDeleteView.as_view(), name='purchase_delete'),
    
    # URL untuk autocomplete
    path('api/item-autocomplete/', views.item_autocomplete_view, name='item_autocomplete'),
]