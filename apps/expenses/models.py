# apps/expenses/models.py

from django.db import models
from django.conf import settings
from django.utils import timezone

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=200, unique=True)
    class Meta:
        verbose_name_plural = "Expense Categories"
    def __str__(self):
        return self.name

class RecurringExpense(models.Model):
    """
    Blueprint/Jadwal Rutin (Gaji, Wifi, Sewa).
    """
    name = models.CharField(max_length=200, help_text="Contoh: Gaji Miko")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Tanggal jatuh tempo setiap bulan (1-28)
    due_date_day = models.PositiveIntegerField(
        default=1, 
        help_text="Tanggal jatuh tempo setiap bulan (misal: 25)"
    )
    
    is_active = models.BooleanField(default=True, help_text="Matikan jika karyawan resign atau layanan berhenti")
    description = models.TextField(blank=True)

    def __str__(self):
        status = "Aktif" if self.is_active else "Non-Aktif"
        return f"{self.name} (Tgl {self.due_date_day}) - {status}"

class Expense(models.Model):
    """
    Tiket Transaksi Pengeluaran (Bisa dari Recurring, bisa Manual).
    """
    class StatusChoices(models.TextChoices):
        PENDING = 'PENDING', 'Belum Dibayar (Hutang)'
        PAID = 'PAID', 'Sudah Dibayar (Lunas)'

    title = models.CharField(max_length=200, default="Pengeluaran")
    category = models.ForeignKey(ExpenseCategory, on_delete=models.PROTECT)
    
    # Link ke sumber rutin (Optional, agar tau ini gaji bulan apa)
    recurring_source = models.ForeignKey(RecurringExpense, on_delete=models.SET_NULL, null=True, blank=True)
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PAID)
    
    # Kapan harus dibayar (Untuk filter PENDING)
    due_date = models.DateField(default=timezone.now, help_text="Tanggal jatuh tempo")
    
    # Kapan uang benar-benar keluar (Untuk Laporan Keuangan)
    payment_date = models.DateField(null=True, blank=True, help_text="Tanggal pembayaran real")
    
    description = models.TextField(blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ['-due_date']

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.status})"