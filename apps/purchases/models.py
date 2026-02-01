# apps/purchases/models.py

from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.master_data.models import Vendor, Mechanic # Import Mechanic
from apps.inventory.models import InventoryItem

class PurchaseOrder(models.Model):
    """
    Model untuk mencatat pembelian barang dari vendor.
    Stok akan bertambah hanya jika status menjadi COMPLETED.
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    vendor = models.ForeignKey(Vendor, on_delete=models.PROTECT)
    order_date = models.DateTimeField(default=timezone.now)
    expected_delivery_date = models.DateField(null=True, blank=True)

    # --- TRACKING PEMBELI (UPDATE BARU) ---
    # Opsi 1: Pilih dari data Mekanik
    purchaser_mechanic = models.ForeignKey(
        Mechanic, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Pilih jika yang belanja adalah Montir"
    )
    # Opsi 2: Isi manual teks (misal: 'Pak Budi' atau 'Admin Gudang')
    purchaser_custom = models.CharField(
        max_length=100, 
        blank=True, 
        help_text="Isi manual jika yang belanja bukan Montir terdaftar"
    )

    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-order_date']

    def __str__(self):
        return f"PO-{self.id} ke {self.vendor.name if self.vendor else 'N/A'}"

    @property
    def purchaser_name(self):
        """Helper untuk menampilkan nama pembeli di template"""
        if self.purchaser_mechanic:
            return self.purchaser_mechanic.name
        return self.purchaser_custom or "-"

    def get_items_used_in_transactions(self):
        """
        Cek apakah barang-barang dari PO ini sudah digunakan di transaksi.
        Return: Dict dengan item_id, item_name, dan qty yang sudah dipakai
        """
        from apps.transactions.models import TransactionItem, Transaction
        
        # Ambil semua item yang ada di PO ini
        po_item_ids = self.items.values_list('item_id', flat=True)
        
        # Cari di transaksi yang PENDING atau COMPLETED (transaksi aktif)
        used_items = TransactionItem.objects.filter(
            item_id__in=po_item_ids,
            transaction__status__in=[Transaction.StatusChoices.PENDING, Transaction.StatusChoices.COMPLETED]
        ).select_related('item', 'transaction').values('item_id', 'item__name').distinct()
        
        return list(used_items)

    def has_items_used_in_transactions(self):
        """
        Check apakah ada barang dari PO yang sudah dipakai di transaksi aktif.
        Return: True jika ada, False jika tidak
        """
        return len(self.get_items_used_in_transactions()) > 0

    def get_items_used_in_transactions_detail(self):
        """
        Get detail lengkap barang yang sudah dipakai beserta jumlahnya.
        Return: List of dict dengan item info dan qty yang dipakai
        """
        from apps.transactions.models import TransactionItem, Transaction
        from django.db.models import Sum
        
        po_item_ids = self.items.values_list('item_id', flat=True)
        
        # Agregasi: total qty per item di transaksi aktif
        used_summary = TransactionItem.objects.filter(
            item_id__in=po_item_ids,
            transaction__status__in=[Transaction.StatusChoices.PENDING, Transaction.StatusChoices.COMPLETED]
        ).values('item_id', 'item__name').annotate(
            total_qty_used=Sum('quantity')
        ).order_by('item__name')
        
        return list(used_summary)


class PurchaseOrderItem(models.Model):
    """
    Item barang yang dibeli dari vendor.
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