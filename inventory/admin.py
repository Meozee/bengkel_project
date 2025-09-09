# inventory/admin.py

from django.contrib import admin
from .models import Merek, Kategori, Supplier, Produk, PergerakanStok

@admin.register(Merek)
class MerekAdmin(admin.ModelAdmin):
    search_fields = ['nama']

@admin.register(Kategori)
class KategoriAdmin(admin.ModelAdmin):
    search_fields = ['nama']

@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    search_fields = ['nama', 'kontak']
    list_display = ('nama', 'kontak', 'alamat')

@admin.register(Produk)
class ProdukAdmin(admin.ModelAdmin):
    list_display = ('nama_produk', 'merek', 'kategori', 'tipe', 'harga_jual_standar', 'ambang_batas_stok')
    list_filter = ('tipe', 'kategori', 'merek')
    search_fields = ('nama_produk', 'kode_produk')
    readonly_fields = ('kode_produk', 'created_at', 'updated_at')
    autocomplete_fields = ['merek', 'kategori']

@admin.register(PergerakanStok)
class PergerakanStokAdmin(admin.ModelAdmin):
    list_display = ('produk', 'jenis', 'jumlah', 'supplier', 'tanggal', 'dibuat_oleh')
    list_filter = ('jenis', 'tanggal')
    autocomplete_fields = ['produk', 'supplier', 'dibuat_oleh']
    readonly_fields = ('tanggal',)