# apps/expenses/urls.py

from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # URL utama (Tabbed List)
    path('', views.expense_index, name='expense_index'),
    
    # URL CRUD untuk Expense
    path('create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('update/<int:pk>/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('delete/<int:pk>/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # URL CRUD untuk ExpenseCategory
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),
]