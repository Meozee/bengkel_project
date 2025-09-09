# users/urls.py

from django.urls import path
from . import views

app_name = 'users'
urlpatterns = [
    # Read (List)
    path('', views.user_management_view, name='user_management'),

    # Customer CRUD
    path('customer/add/', views.customer_create_view, name='customer_create'),
    path('customer/<int:pk>/update/', views.customer_update_view, name='customer_update'),
    path('customer/<int:pk>/delete/', views.customer_delete_view, name='customer_delete'),

    # User CRUD
    path('user/add/', views.user_create_view, name='user_create'),
    path('user/<int:pk>/update/', views.user_update_view, name='user_update'),
    path('user/<int:pk>/delete/', views.user_delete_view, name='user_delete'),
]