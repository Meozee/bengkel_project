from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    # Inventory Item URLs
    path('', views.inventory_list, name='inventory_list'),
    path('add/', views.inventory_create, name='inventory_create'),
    path('<int:pk>/', views.inventory_detail, name='inventory_detail'),
    path('<int:pk>/update/', views.inventory_update, name='inventory_update'),
    path('<int:pk>/delete/', views.inventory_delete, name='inventory_delete'),

    # Category URLs
    path('categories/', views.category_list, name='category_list'),
    # Gunakan 'category_form' untuk add dan edit
    path('categories/add/', views.category_form, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_form, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
]