from django.urls import path
from . import views

app_name = 'master_data'

urlpatterns = [
    # Halaman Utama
    path('', views.master_data_index, name='master_data_index'),

    # Customer URLs
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/new/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('customers/<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('customers/<int:pk>/delete/', views.CustomerDeleteView.as_view(), name='customer_delete'),

    # Mechanic URLs
    path('mechanics/', views.MechanicListView.as_view(), name='mechanic_list'),
    path('mechanics/new/', views.MechanicCreateView.as_view(), name='mechanic_create'),
    path('mechanics/<int:pk>/edit/', views.MechanicUpdateView.as_view(), name='mechanic_update'),
    path('mechanics/<int:pk>/delete/', views.MechanicDeleteView.as_view(), name='mechanic_delete'),

    # Vehicle URLs
    path('vehicles/', views.VehicleListView.as_view(), name='vehicle_list'),
    path('vehicles/new/', views.VehicleCreateView.as_view(), name='vehicle_create'),
    path('vehicles/<int:pk>/edit/', views.VehicleUpdateView.as_view(), name='vehicle_update'),
    path('vehicles/<int:pk>/delete/', views.VehicleDeleteView.as_view(), name='vehicle_delete'),
    
    # Service URLs
    path('services/', views.ServiceListView.as_view(), name='service_list'),
    path('services/new/', views.ServiceCreateView.as_view(), name='service_create'),
    path('services/<int:pk>/edit/', views.ServiceUpdateView.as_view(), name='service_update'),
    path('services/<int:pk>/delete/', views.ServiceDeleteView.as_view(), name='service_delete'),

    # Vendor URLs
    path('vendors/', views.VendorListView.as_view(), name='vendor_list'),
    path('vendors/new/', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendors/<int:pk>/edit/', views.VendorUpdateView.as_view(), name='vendor_update'),
    path('vendors/<int:pk>/delete/', views.VendorDeleteView.as_view(), name='vendor_delete'),
]