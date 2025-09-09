# transactions/models.py

from django.db import models
from django.conf import settings
from users.models import Customer, User
# PERBAIKAN: Impor Produk, bukan Sparepart
from inventory.models import Produk 

class Transaksi(models.Model):
    class StatusChoices(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        COMPLETED = 'completed', 'Completed'
        CANCELLED = 'cancelled', 'Cancelled'

    class ServiceChoices(models.TextChoices):
        RUTIN = 'rutin', 'Service Rutin'
        PERBAIKAN = 'perbaikan', 'Perbaikan'
        GANTI_OLI = 'ganti_oli', 'Ganti Oli'
        LAINNYA = 'lainnya', 'Lainnya'

    kode_transaksi = models.CharField(max_length=20, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, related_name='transaksi_set')
    montir = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='transaksi_montir_set',
        limit_choices_to={'role': 'montir'}
    )

    jenis_service = models.CharField(max_length=20, choices=ServiceChoices.choices, default=ServiceChoices.RUTIN)
    status = models.CharField(max_length=20, choices=StatusChoices.choices, default=StatusChoices.PENDING)

    # PERBAIKAN: ManyToManyField sekarang ke Produk
    spareparts = models.ManyToManyField(Produk, through='TransaksiProduk', related_name='transaksi_set')
    biaya_jasa = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    rating_customer = models.PositiveSmallIntegerField(null=True, blank=True)
    komentar_customer = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def total_harga_sparepart(self):
        total = self.transaksiproduk_set.aggregate(
            total_harga=models.Sum(models.F('jumlah_digunakan') * models.F('harga_satuan'))
        )['total_harga']
        return total if total is not None else 0

    @property
    def total_harga(self):
        return self.total_harga_sparepart + self.biaya_jasa

    def __str__(self):
        return self.kode_transaksi

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Transaksi"

# PERBAIKAN: Ganti nama model dan ForeignKey
class TransaksiProduk(models.Model):
    transaksi = models.ForeignKey(Transaksi, on_delete=models.CASCADE)
    produk = models.ForeignKey(Produk, on_delete=models.CASCADE)
    jumlah_digunakan = models.PositiveIntegerField(default=1)
    harga_satuan = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"{self.jumlah_digunakan} x {self.produk.nama_produk} di {self.transaksi.kode_transaksi}"

    @property
    def subtotal(self):
        return self.jumlah_digunakan * self.harga_satuan

    class Meta:
        unique_together = ('transaksi', 'produk')
        verbose_name_plural = "Produk Transaksi"