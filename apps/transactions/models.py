# ===== apps/transactions/models.py =====
from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.master_data.models import Customer, Vehicle, Mechanic, Service
from apps.inventory.models import InventoryItem


class Transaction(models.Model):
    """
    Model utama transaksi penjualan barang & jasa.
    Stok akan dikurangi hanya saat status berubah menjadi PAID (lihat sinyal).
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        PAID = 'PAID', 'Paid'
        CANCELLED = 'CANCELLED', 'Cancelled'

    invoice_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True)

    transaction_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                       help_text="Biaya lain-lain")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), 
                                         help_text="Potongan harga final")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-transaction_date']

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.customer.name if self.customer else 'N/A'}"


class TransactionItem(models.Model):
    """Item barang yang dijual di transaksi."""
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga item saat transaksi")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'), 
                                             help_text="Diskon persen (contoh: 10 = 10%)")

    class Meta:
        verbose_name = "Transaction Item"
        verbose_name_plural = "Transaction Items"

    def __str__(self):
        return f"{self.quantity}x {self.item.name} untuk {self.transaction.invoice_number}"

    @property
    def subtotal(self):
        price_before_discount = Decimal(self.quantity) * Decimal(self.unit_price)
        discount_amount = price_before_discount * (self.discount_percentage / Decimal('100'))
        return price_before_discount - discount_amount


class TransactionService(models.Model):
    """Layanan (service) yang dijual bersama transaksi."""
    transaction = models.ForeignKey(Transaction, related_name='services', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)

    quantity = models.PositiveIntegerField(default=1)  # ✅ TAMBAHKAN FIELD INI
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga jasa saat transaksi")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    class Meta:
        verbose_name = "Transaction Service"
        verbose_name_plural = "Transaction Services"

    def __str__(self):
        return f"{self.service.name} ({self.transaction.invoice_number})"

    @property
    def subtotal(self):
        price_before_discount = Decimal(self.quantity) * Decimal(self.unit_price)
        discount_amount = price_before_discount * (self.discount_percentage / Decimal('100'))
        return price_before_discount - discount_amount
