# apps/transactions/urls.py

from django.urls import path
from . import views

app_name = 'transactions'

urlpatterns = [
    # ==============================
    # 1. HALAMAN UTAMA (LIST & DETAIL)
    # ==============================
    path('', views.transaction_list, name='transaction_list'),
    path('detail/<int:pk>/', views.transaction_detail, name='transaction_detail'),

    # ==============================
    # 2. CRUD (CREATE, EDIT, DELETE)
    # ==============================
    path('create/', views.transaction_create, name='transaction_create'),
    path('edit/<int:pk>/', views.transaction_edit, name='transaction_edit'),
    path('delete/<int:pk>/', views.transaction_delete, name='transaction_delete'),

    # ==============================
    # 3. AKSI KHUSUS (STATUS & PRINT)
    # ==============================
    # Mengubah status (Pending -> Completed -> Cancelled)
    path('status/<int:pk>/<str:new_status>/', views.update_status, name='update_status'),
    
    # Print Langsung ke USB (Thermal Printer 58mm)
    path('print-direct/<int:pk>/', views.transaction_print_direct, name='transaction_print_direct'),
    
    # Print via Browser/HTML (Backup/Preview)
    path('print/<int:pk>/', views.transaction_print, name='transaction_print'),

    # ==============================
    # 4. API ENDPOINTS (AJAX - JSON)
    # ==============================
    # Digunakan oleh JavaScript di form untuk auto-fill harga
    path('api/item-price/<int:item_id>/', views.api_get_item_price, name='api_get_item_price'),
    path('api/service-price/<int:service_id>/', views.api_get_service_price, name='api_get_service_price'),
]