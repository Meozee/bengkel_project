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
    is_active = models.BooleanField(default=True, help_text="Jika tidak dicentang, kategori ini akan disembunyikan.")

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

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

    # --- PRICING ---
    buy_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    sell_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga jual barang saja")
    
    # 🔥 CHANGE: Field install_price & install_service_name DIHAPUS.
    # Kita menggunakan model VehicleServicePrice (One-to-Many) di bawah.

    quantity = models.PositiveIntegerField(default=0)
    reorder_threshold = models.PositiveIntegerField(default=10)
    
    extra_specs = models.JSONField(default=dict, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Tanggal Masuk")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.sku or 'No SKU'})"

    @property
    def is_low_stock(self):
        return self.quantity <= self.reorder_threshold


class VehicleServicePrice(models.Model):
    """
    Tabel ini menyimpan variasi harga jasa pasang untuk satu barang.
    Contoh: 
    - Item: Aki GS Astra -> Vehicle: NMAX -> Price: 20.000
    - Item: Aki GS Astra -> Vehicle: Beat -> Price: 10.000
    """
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name='service_prices')
    vehicle_type = models.CharField(max_length=100, help_text="Contoh: NMAX, Beat, Sport 150cc")
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Harga jasa pasang")
    
    def __str__(self):
        return f"{self.vehicle_type}: {self.price}"


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