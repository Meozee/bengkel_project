# apps/reports/urls.py

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.report_index, name='report_index'),
    
    # Financial (Laba Rugi)
    path('financial/', views.financial_report_view, name='financial_report'),
    path('export/financial/', views.export_financial_report, name='export_financial'),
    
    # Inventory & Dead Stock
    path('inventory/', views.inventory_report_view, name='inventory_report'),
    path('export/inventory/', views.export_inventory_report, name='export_inventory'),
    path('dead-stock/', views.dead_stock_view, name='dead_stock_report'), 
    path('export/dead-stock/', views.export_dead_stock, name='export_dead_stock'), 
    path('inventory/export/excel/', views.export_inventory_excel, name='export_inventory_excel'),

    # Sales & Expense
    path('sales/', views.sales_report_view, name='sales_report'), 
    path('export/sales/', views.export_sales_report, name='export_sales'), 
    path('expense-breakdown/', views.expense_breakdown_view, name='expense_breakdown'), 
    path('export/expense-breakdown/', views.export_expense_breakdown, name='export_expense_breakdown'), 

    # Mechanic
    path('mechanic-performance/', views.mechanic_performance_view, name='mechanic_performance'),
    path('export/mechanic/', views.export_mechanic_report, name='export_mechanic'),
    
    # Vehicle History (Menggantikan Customer Report)
    path('vehicle-history/', views.vehicle_history_view, name='vehicle_history'),
    # Alias agar link lama (jika ada) tidak error
    path('customer/', views.customer_report_view, name='customer_report'),
    path('export/customer/', views.export_customer_report, name='export_customer'),
]