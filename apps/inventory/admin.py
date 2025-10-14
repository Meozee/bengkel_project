# apps/inventory/admin.py

from django.contrib import admin
from django.db.models import F
from .models import Category, InventoryItem

# 1. Buat class filter kustom di sini
class LowStockFilter(admin.SimpleListFilter):
    title = 'stock status' # Judul filter di sidebar
    parameter_name = 'stock_status' # Parameter di URL

    def lookups(self, request, model_admin):
        # Opsi filter yang akan muncul: (nilai_di_url, teks_yang_terlihat)
        return (
            ('low', 'Low Stock'),
        )

    def queryset(self, request, queryset):
        # Logika filter: jika nilainya 'low', filter item yang stoknya <= ambang batas
        if self.value() == 'low':
            return queryset.filter(quantity__lte=F('reorder_threshold'))
        return queryset

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'buy_price', 'sell_price', 'quantity', 'is_low_stock')
    search_fields = ('name', 'sku')
    list_filter = ('category', LowStockFilter)
    
    # Hapus list_editable karena quantity tidak boleh diedit manual lagi
    # list_editable = ('sell_price', 'quantity') 
    
    # Buat field-field ini hanya bisa dilihat, tidak bisa diedit
    readonly_fields = ('quantity', 'buy_price')