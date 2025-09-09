# transactions/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # URL untuk menampilkan daftar transaksi
    # Alamatnya akan menjadi /transactions/
    path('', views.transaction_list_view, name='transaction_list'),
    path('add/', views.transaction_create_view, name='transaction_create'),

]