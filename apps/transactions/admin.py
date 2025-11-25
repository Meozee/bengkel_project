# apps/transactions/admin.py

from django.contrib import admin
from .models import Transaction, TransactionItem, TransactionService

class ItemInline(admin.TabularInline):
    model = TransactionItem
    extra = 0

class ServiceInline(admin.TabularInline):
    model = TransactionService
    extra = 0

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'created_at', 'status', 'total_amount')
    list_filter = ('status', 'created_at', 'mechanic')
    inlines = [ItemInline, ServiceInline]
    readonly_fields = ('invoice_number', 'total_amount', 'created_at', 'completed_at')