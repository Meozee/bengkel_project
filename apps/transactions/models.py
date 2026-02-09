from decimal import Decimal
from django.db import models
from django.utils import timezone

# Import model dari app lain
from apps.master_data.models import Customer, Vehicle, Mechanic, Service
from apps.inventory.models import InventoryItem, VehicleServicePrice

class Transaction(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending (Proses)'
        COMPLETED = 'COMPLETED', 'Completed (Selesai)'
        CANCELLED = 'CANCELLED', 'Cancelled (Batal)'

    # ==========================
    # 1. IDENTITAS TRANSAKSI
    # ==========================
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True)

    # ==========================
    # 2. WAKTU & STATUS
    # ==========================
    created_at = models.DateTimeField(auto_now_add=True)  
    updated_at = models.DateTimeField(auto_now=True)      
    completed_at = models.DateTimeField(null=True, blank=True) 
    
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )

    # ==========================
    # 3. KEUANGAN
    # ==========================
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Biaya tambahan lain-lain (Global)")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Diskon final (Nominal Rupiah)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True, help_text="Catatan keluhan atau perbaikan")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    # ==========================
    # LOGIC METHODS
    # ==========================

    def save(self, *args, **kwargs):
        """Generate Invoice Number otomatis: INV-YYYYMM-0001"""
        if not self.invoice_number:
            now = timezone.now()
            month_str = now.strftime('%Y%m')
            last_txn = Transaction.objects.filter(invoice_number__startswith=f"INV-{month_str}").order_by('-id').first()
            
            if last_txn:
                try:
                    last_seq = int(last_txn.invoice_number.split('-')[-1])
                    new_seq = last_seq + 1
                except ValueError:
                    new_seq = 1
            else:
                new_seq = 1
            
            self.invoice_number = f"INV-{month_str}-{new_seq:04d}"
        
        super().save(*args, **kwargs)

    @property
    def duration_minutes(self):
        """Menghitung durasi pengerjaan dalam menit"""
        if self.completed_at and self.created_at:
            diff = self.completed_at - self.created_at
            return int(diff.total_seconds() / 60)
        return 0

    def can_be_edited(self):
        return self.status == self.StatusChoices.PENDING

    def can_be_deleted(self):
        return self.status == self.StatusChoices.PENDING


class TransactionItem(models.Model):
    """Detail Barang/Sparepart yang dibeli"""
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT) 
    quantity = models.PositiveIntegerField(default=1)
    
    # 🔥 CHANGE: Menggunakan ForeignKey ke VehicleServicePrice untuk Dropdown Jasa
    install_service = models.ForeignKey(
        VehicleServicePrice, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        help_text="Pilihan harga jasa pasang (opsional)"
    )

    # Harga Snapshot (disimpan saat transaksi terjadi)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.item.name} ({self.quantity})"

    @property
    def subtotal(self):
        price = Decimal(self.quantity) * Decimal(self.unit_price)
        disc = price * (self.discount_percentage / Decimal('100'))
        return price - disc


class TransactionService(models.Model):
    """Detail Jasa Service Umum yang dilakukan"""
    transaction = models.ForeignKey(Transaction, related_name='services', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"{self.service.name} ({self.quantity})"

    @property
    def subtotal(self):
        price = Decimal(self.quantity) * Decimal(self.unit_price)
        disc = price * (self.discount_percentage / Decimal('100'))
        return price - disc


class TransactionMisc(models.Model):
    """Item Non-Stok / Biaya Lain-lain"""
    transaction = models.ForeignKey(Transaction, related_name='miscs', on_delete=models.CASCADE)
    description = models.CharField(max_length=255, help_text="Nama barang/biaya")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    
    def __str__(self):
        return f"{self.description} ({self.quantity})"

    @property
    def subtotal(self):
        return Decimal(self.quantity) * Decimal(self.unit_price)


class TransactionItemSource(models.Model):
    """Mencatat histori FIFO: Mengambil barang dari PO mana"""
    transaction_item = models.ForeignKey(TransactionItem, related_name='sources', on_delete=models.CASCADE)
    purchase_order_item = models.ForeignKey('purchases.PurchaseOrderItem', on_delete=models.CASCADE)
    quantity_taken = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.quantity_taken} dari PO#{self.purchase_order_item.purchase_order_id}"