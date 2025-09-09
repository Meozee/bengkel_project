# transactions/admin.py

from django.contrib import admin
# PERBAIKAN: Impor TransaksiProduk, bukan TransaksiSparepart
from .models import Transaksi, TransaksiProduk

class TransaksiProdukInline(admin.TabularInline):
    # PERBAIKAN: Gunakan model TransaksiProduk
    model = TransaksiProduk
    extra = 1
    autocomplete_fields = ['produk']

@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    inlines = [TransaksiProdukInline]
    list_display = ('kode_transaksi', 'customer', 'montir', 'status', 'jenis_service', 'created_at')
    list_filter = ('status', 'jenis_service', 'created_at')
    search_fields = ('kode_transaksi', 'customer__nama', 'montir__nama_lengkap')
    readonly_fields = ('kode_transaksi', 'created_at', 'updated_at')