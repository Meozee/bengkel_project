# apps/transactions/models.py

from decimal import Decimal
from django.db import models
from django.utils import timezone
from apps.master_data.models import Customer, Vehicle, Mechanic, Service
from apps.inventory.models import InventoryItem

class Transaction(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Pending (Proses)'
        COMPLETED = 'COMPLETED', 'Completed (Selesai)'
        CANCELLED = 'CANCELLED', 'Cancelled (Batal)'

    # Identitas
    invoice_number = models.CharField(max_length=50, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    vehicle = models.ForeignKey(Vehicle, on_delete=models.SET_NULL, null=True, blank=True)
    mechanic = models.ForeignKey(Mechanic, on_delete=models.SET_NULL, null=True, blank=True)

    # Waktu & Status
    created_at = models.DateTimeField(auto_now_add=True) # Waktu Masuk
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True) # Waktu Selesai (Otomatis diisi sistem)
    
    status = models.CharField(
        max_length=20, 
        choices=StatusChoices.choices, 
        default=StatusChoices.PENDING
    )

    # Keuangan
    other_charges = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Biaya tambahan lain-lain")
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'), help_text="Diskon final (Rupiah)")
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0.00'))

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.invoice_number

    def save(self, *args, **kwargs):
        # Generate Invoice Number Otomatis: INV-YYYYMM-0001
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
        """Menghitung durasi pengerjaan (KPI Montir)"""
        if self.completed_at and self.created_at:
            diff = self.completed_at - self.created_at
            return int(diff.total_seconds() / 60)
        return 0


class TransactionItem(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='items', on_delete=models.CASCADE)
    item = models.ForeignKey(InventoryItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    @property
    def subtotal(self):
        price = Decimal(self.quantity) * Decimal(self.unit_price)
        disc = price * (self.discount_percentage / Decimal('100'))
        return price - disc

class TransactionService(models.Model):
    transaction = models.ForeignKey(Transaction, related_name='services', on_delete=models.CASCADE)
    service = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))

    @property
    def subtotal(self):
        price = Decimal(self.quantity) * Decimal(self.unit_price)
        disc = price * (self.discount_percentage / Decimal('100'))
        return price - disc