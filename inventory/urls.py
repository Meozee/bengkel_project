# inventory/urls.py

from django.urls import path
from . import views

app_name = 'inventory'
urlpatterns = [
    # Halaman utama inventaris (dengan tab)
    path('', views.inventory_dashboard_view, name='inventory_dashboard'),

    # URL Produk
    path('produk/add/', views.produk_create_view, name='produk_create'),
    path('produk/<int:pk>/update/', views.produk_update_view, name='produk_update'),
    path('produk/<int:pk>/delete/', views.produk_delete_view, name='produk_delete'),

    # URL Data Master (untuk form action)
    path('merek/add/', views.merek_create_view, name='merek_create'),
    path('merek/<int:pk>/delete/', views.merek_delete_view, name='merek_delete'),
    path('kategori/add/', views.kategori_create_view, name='kategori_create'),
    path('kategori/<int:pk>/delete/', views.kategori_delete_view, name='kategori_delete'),
    path('supplier/add/', views.supplier_create_view, name='supplier_create'),
    path('supplier/<int:pk>/delete/', views.supplier_delete_view, name='supplier_delete'),
]