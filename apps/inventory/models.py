# apps/inventory/models.py

from decimal import Decimal
from django.db import models

class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    class ItemTypeChoices(models.TextChoices):
        CONSUMABLE = 'CONSUMABLE', 'Habis Pakai'
        NON_CONSUMABLE = 'NON_CONSUMABLE', 'Tidak Habis Pakai'

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    name = models.CharField(max_length=255)
    item_type = models.CharField(max_length=20, choices=ItemTypeChoices.choices, default=ItemTypeChoices.CONSUMABLE)
    sku = models.CharField(max_length=100, unique=True, blank=True, null=True, help_text="Stock Keeping Unit")
    description = models.TextField(blank=True)

    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'), help_text="Harga beli rata-rata dari supplier")
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga jual ke pelanggan")

    quantity = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10, help_text="Batas minimum stok sebelum notifikasi")

    def __str__(self):
        return f"{self.name} (Stok: {self.quantity})"

    @property
    def is_low_stock(self):
        """Properti untuk mengecek apakah stok sudah di bawah ambang batas."""
        return self.quantity <= self.reorder_threshold


class InventoryLog(models.Model):
    """
    Audit log untuk setiap perubahan stok agar mudah trace back.
    change = signed integer (positif = tambah, negatif = kurang)
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='logs')
    change = models.IntegerField()
    before = models.IntegerField()
    after = models.IntegerField()
    source_type = models.CharField(max_length=50)  # e.g., "PURCHASE", "TRANSACTION", "MANUAL"
    source_id = models.PositiveIntegerField(null=True, blank=True)  # id PO / Transaction
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        sign = '+' if self.change >= 0 else ''
        return f"{self.item.name}: {sign}{self.change} ({self.before} -> {self.after}) [{self.source_type}#{self.source_id}]"
