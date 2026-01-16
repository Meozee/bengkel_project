from decimal import Decimal
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    required_specs = models.CharField(
        max_length=500,
        blank=True,
        help_text="Masukkan nama spesifikasi dipisahkan koma. Contoh: Volume, SAE, Type"
    )
    # ✅ SOFT DELETE FIELD
    is_active = models.BooleanField(default=True, help_text="Jika tidak dicentang, kategori ini akan disembunyikan.")

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

    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)

    quantity = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10)
    
    # 🔥 FIX: Tambahkan null=True untuk backward compatibility
    extra_specs = models.JSONField(default=dict, blank=True, null=True)

    # ✅ SOFT DELETE FIELD
    is_active = models.BooleanField(default=True, help_text="Jika Non-Aktif, item tidak akan muncul di list penjualan.")

    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_threshold


class InventoryLog(models.Model):
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='logs')
    change = models.IntegerField()
    before = models.IntegerField()
    after = models.IntegerField()
    source_type = models.CharField(max_length=50)
    source_id = models.PositiveIntegerField(null=True, blank=True)
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-timestamp',)

    def __str__(self):
        sign = '+' if self.change >= 0 else ''
        return f"{self.item.name}: {sign}{self.change} ({self.before} -> {self.after})"