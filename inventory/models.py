# inventory/models.py

from django.db import models
from django.utils import timezone
from django.db.models import Sum
from django.conf import settings

# --- MODEL DATA MASTER ---
class Merek(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nama
    class Meta: ordering = ['nama']

class Kategori(models.Model):
    nama = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.nama
    class Meta:
        verbose_name_plural = "Kategori"
        ordering = ['nama']

class Supplier(models.Model):
    nama = models.CharField(max_length=150, unique=True)
    kontak = models.CharField(max_length=20, blank=True)
    alamat = models.TextField(blank=True)
    def __str__(self): return self.nama
    class Meta: ordering = ['nama']

class TipePembelian(models.Model):
    nama = models.CharField(max_length=50, unique=True)
    def __str__(self): return self.nama
    class Meta:
        verbose_name_plural = "Tipe Pembelian"
        ordering = ['nama']

# --- MODEL PRODUK (KATALOG) ---
class Produk(models.Model):
    class TipeProduk(models.TextChoices):
        SPAREPART = 'sparepart', 'Sparepart (Habis Pakai)'
        TOOLS = 'tools', 'Alat (Tidak Habis Pakai)'

    nama_produk = models.CharField(max_length=255, unique=True)
    merek = models.ForeignKey(Merek, on_delete=models.PROTECT)
    kategori = models.ForeignKey(Kategori, on_delete=models.PROTECT)
    tipe = models.CharField(max_length=20, choices=TipeProduk.choices)
    kode_produk = models.CharField(max_length=20, unique=True, blank=True, editable=False)
    ambang_batas_stok = models.PositiveIntegerField(default=5)
    harga_jual_standar = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)

    # V TAMBAHKAN KEMBALI DUA FIELD INI V
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def stok_saat_ini(self):
        pergerakan = self.pergerakan.all()
        masuk = pergerakan.filter(jenis='MASUK').aggregate(total=Sum('jumlah'))['total'] or 0
        keluar = pergerakan.filter(jenis='KELUAR').aggregate(total=Sum('jumlah'))['total'] or 0
        koreksi = pergerakan.filter(jenis='KOREKSI').aggregate(total=Sum('jumlah'))['total'] or 0
        return masuk - keluar + koreksi

    def save(self, *args, **kwargs):
        if not self.kode_produk:
            last = Produk.objects.all().order_by('id').last()
            next_id = (last.id + 1) if last else 1
            self.kode_produk = f"PROD-{next_id:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nama_produk} ({self.merek.nama})"

    class Meta:
        ordering = ['nama_produk']

# --- MODEL PERGERAKAN STOK ---
class PergerakanStok(models.Model):
    class Jenis(models.TextChoices):
        MASUK = 'MASUK', 'Stok Masuk (Pembelian)'
        KELUAR = 'KELUAR', 'Stok Keluar (Penjualan)'
        KOREKSI = 'KOREKSI', 'Koreksi Stok'

    produk = models.ForeignKey(Produk, on_delete=models.PROTECT, related_name="pergerakan")
    jenis = models.CharField(max_length=10, choices=Jenis.choices)
    jumlah = models.IntegerField()
    harga_beli_satuan = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tipe_pembelian = models.ForeignKey(TipePembelian, on_delete=models.SET_NULL, null=True, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True)
    tanggal = models.DateTimeField(default=timezone.now)
    keterangan = models.TextField(blank=True)
    dibuat_oleh = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_jenis_display()}: {self.jumlah} x {self.produk.nama_produk}"

    class Meta:
        ordering = ['-tanggal']
        verbose_name_plural = "Pergerakan Stok"