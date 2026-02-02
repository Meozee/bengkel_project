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
        Cek apakah stok SPESIFIK dari PO ini sudah diambil oleh transaksi.
        Menggunakan tabel TransactionItemSource (FIFO Logic).
        """
        from apps.transactions.models import TransactionItemSource
        
        # Cek apakah ada 'jejak' pengambilan barang dari PO ini
        return TransactionItemSource.objects.filter(
            purchase_order_item__purchase_order=self
        ).exists()

    def get_items_used_in_transactions_detail(self):
        """
        Ambil detail barang apa saja dari PO ini yang sudah laku terjual.
        """
        from apps.transactions.models import TransactionItemSource
        
        # Grouping berdasarkan nama item dan jumlah yang diambil
        return TransactionItemSource.objects.filter(
            purchase_order_item__purchase_order=self
        ).values(
            name=F('purchase_order_item__item__name') # Alias biar mudah dipanggil di views
        ).annotate(
            total_qty_used=Sum('quantity_taken')
        ).order_by('name')


class PurchaseOrderItem(models.Model):
    """
    Item barang yang dibeli dari vendor.
    """
    purchase_order = models.ForeignKey(PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity_remaining = models.PositiveIntegerField(default=0, help_text="Sisa stok dari batch PO ini")
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