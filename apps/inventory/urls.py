# apps/inventory/urls.py

from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Inventory Item URLs
    path('', views.inventory_list, name='inventory_list'),
    path('item/add/', views.inventory_create, name='inventory_add'),
    path('item/<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('item/<int:pk>/edit/', views.inventory_update, name='inventory_update'),
    path('item/<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/add/', views.category_form, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_form, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    # --- TAMBAHAN BARU: API APIAN SEDERHANA ---
    path('api/get-category-specs/<int:category_id>/', views.get_category_specs, name='get_category_specs'),
]