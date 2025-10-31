from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Web Views
    path('', views.report_index, name='report_index'),
    path('financial/', views.financial_report_view, name='financial_report'),
    path('inventory/', views.inventory_report_view, name='inventory_report'),
    path('mechanic-performance/', views.mechanic_performance_view, name='mechanic_performance'),
    path('customer/', views.customer_report_view, name='customer_report'),

    # Export Endpoints
    path('export/financial/', views.export_financial_report, name='export_financial'),
    path('export/inventory/', views.export_inventory_report, name='export_inventory'),
    path('export/customer/', views.export_customer_report, name='export_customer'),
]