# analytics/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, F
from decimal import Decimal

from transactions.models import Transaksi
# PERBAIKAN: Impor Produk, bukan Sparepart
from inventory.models import Produk 
from users.models import User

@login_required
def dashboard_view(request):
    today = timezone.now().date()

    # 1. KPI: Transaksi Hari Ini
    transaksi_hari_ini = Transaksi.objects.filter(created_at__date=today).count()

    # 2. KPI: Pendapatan Bulan Ini
    pendapatan_bulan_ini = Transaksi.objects.filter(
        status='completed',
        created_at__year=today.year,
        created_at__month=today.month
    ).aggregate(
        total_jasa=Sum('biaya_jasa'),
        total_sparepart=Sum(F('transaksiproduk__jumlah_digunakan') * F('transaksiproduk__harga_satuan'))
    )
    total_pendapatan = (pendapatan_bulan_ini['total_jasa'] or Decimal(0)) + \
                       (pendapatan_bulan_ini['total_sparepart'] or Decimal(0))

    # 3. KPI: Stok Hampir Habis
    # PERBAIKAN: Hitung dari model Produk
    stok_hampir_habis = Produk.objects.annotate(
        stok=Sum('pergerakan__jumlah', default=0)
    ).filter(stok__lte=F('ambang_batas_stok')).count()

    # 4. KPI: Montir Aktif
    montir_aktif = User.objects.filter(role='montir', is_active=True).count()

    context = {
        'title': 'Dashboard Utama',
        'transaksi_hari_ini': transaksi_hari_ini,
        'pendapatan_bulan_ini': total_pendapatan,
        'stok_hampir_habis': stok_hampir_habis,
        'montir_aktif': montir_aktif,
    }
    return render(request, 'analytics/dashboard.html', context)