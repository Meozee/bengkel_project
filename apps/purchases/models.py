# apps/purchases/models.py

from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.master_data.models import Vendor
from apps.inventory.models import InventoryItem


class PurchaseOrder(models.Model):
    """
    Model untuk mencatat pembelian barang dari vendor.
    Stok akan bertambah hanya jika status menjadi COMPLETED (lihat sinyal).
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    order_date = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"PO-{self.id} ke {self.vendor.name if self.vendor else 'N/A'} ({self.status})"

    # Tidak perlu override save(); logika stok di-handle oleh sinyal.


class PurchaseOrderItem(models.Model):
    """
    Item barang yang dibeli dari vendor.
    Harga & jumlah stok dicatat pada saat PO dibuat.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga beli barang dari vendor")

    class Meta:
        verbose_name = "Purchase Order Item"
        verbose_name_plural = "Purchase Order Items"

    def __str__(self):
        return f"{self.quantity}x {self.item.name}"

    @property
    def subtotal(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)
