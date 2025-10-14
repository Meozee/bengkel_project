# apps/transactions/admin.py

from django.contrib import admin
from .models import Transaction, TransactionItem, TransactionService

class TransactionItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 1
    # Tampilkan field baru di inline
    fields = ('item', 'quantity', 'unit_price', 'discount_percentage')

class TransactionServiceInline(admin.TabularInline):
    model = TransactionService
    extra = 1
    # Tampilkan field baru di inline
    fields = ('service', 'price', 'discount_percentage')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'mechanic', 'total_amount', 'status', 'transaction_date')
    list_filter = ('status', 'mechanic')
    search_fields = ('invoice_number', 'customer__name', 'vehicle__license_plate')
    inlines = [TransactionItemInline, TransactionServiceInline]
    
    # Buat field total hanya bisa dibaca, dan tambahkan field baru ke form
    readonly_fields = ('total_amount',)
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'status', 'customer', 'vehicle', 'mechanic', 'transaction_date')
        }),
        ('Financials', {
            'fields': ('other_charges', 'discount_amount', 'total_amount')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )