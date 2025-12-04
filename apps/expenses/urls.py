# apps/expenses/urls.py

from django.urls import path
from . import views

app_name = 'expenses'

urlpatterns = [
    # Main Dashboard
    path('', views.expense_index, name='expense_index'),
    
    path('detail/<int:pk>/', views.expense_detail, name='expense_detail'),
    # Action: Pay & Toggle
    path('pay/<int:pk>/', views.pay_expense, name='pay_expense'),
    path('recurring/toggle/<int:pk>/', views.toggle_recurring, name='toggle_recurring'),

    # CRUD Expense (Manual/Tiket)
    path('create/', views.ExpenseCreateView.as_view(), name='expense_create'),
    path('update/<int:pk>/', views.ExpenseUpdateView.as_view(), name='expense_update'),
    path('delete/<int:pk>/', views.ExpenseDeleteView.as_view(), name='expense_delete'),
    
    # CRUD Recurring (Jadwal)
    path('recurring/create/', views.RecurringCreateView.as_view(), name='recurring_create'),
    path('recurring/update/<int:pk>/', views.RecurringUpdateView.as_view(), name='recurring_update'),
    path('recurring/delete/<int:pk>/', views.RecurringDeleteView.as_view(), name='recurring_delete'),

    # CRUD Category
    path('category/create/', views.CategoryCreateView.as_view(), name='category_create'),
    path('category/update/<int:pk>/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('category/delete/<int:pk>/', views.CategoryDeleteView.as_view(), name='category_delete'),
]