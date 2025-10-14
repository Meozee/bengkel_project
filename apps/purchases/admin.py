# apps/purchases/admin.py

from django.contrib import admin
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 1

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'vendor', 'status', 'total_amount', 'order_date')
    list_filter = ('status', 'vendor')
    search_fields = ('id', 'vendor__name')
    inlines = [PurchaseOrderItemInline]
    readonly_fields = ('total_amount',)