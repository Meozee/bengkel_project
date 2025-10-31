# apps/dashboard/views.py

import json
from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta # Perlu install: pip install python-dateutil

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, F, Q, Case, When, DecimalField
from django.db.models.functions import TruncDay

# Import semua model yang relevan
from apps.transactions.models import Transaction, TransactionItem, TransactionService
from apps.expenses.models import Expense
from apps.purchases.models import PurchaseOrder
# BENAR:
from apps.master_data.models import Mechanic, Customer, Service, Vendor
from apps.inventory.models import InventoryItem # <-- Pindahkan InventoryItem ke sini
@login_required
def dashboard_view(request):
    
    # --- 1. Logika Filter Tanggal ---
    
    # Dapatkan parameter 'periode' dari URL, default-nya 'bulan_ini'
    periode = request.GET.get('periode', 'bulan_ini')
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')

    today = timezone.now().date()
    
    # Tentukan rentang tanggal (date_range) berdasarkan filter
    if periode == 'bulan_ini':
        start_date = today.replace(day=1)
        # Pergi ke hari pertama bulan depan, lalu kurangi satu hari
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    elif periode == 'bulan_lalu':
        first_day_current_month = today.replace(day=1)
        end_date = first_day_current_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif periode == 'custom' and custom_start and custom_end:
        start_date = custom_start
        end_date = custom_end
    else: # Default 'keseluruhan'
        periode = 'keseluruhan'
        start_date = None
        end_date = None

    # Buat Q object untuk filter tanggal. Jika 'keseluruhan', Q object kosong
    q_filter_transaksi = Q(transaction_date__date__range=(start_date, end_date)) if start_date else Q()
    q_filter_expense = Q(date__range=(start_date, end_date)) if start_date else Q()
    q_filter_purchase = Q(order_date__date__range=(start_date, end_date)) if start_date else Q()

    # --- 2. Perhitungan KPI (Key Performance Indicators) ---
    
    # Total Pemasukan (dari Transaksi yang PAID)
    total_pemasukan = Transaction.objects.filter(
        q_filter_transaksi, status=Transaction.StatusChoices.PAID
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    # Total Pengeluaran (Gabungan dari Expense + Purchase Order COMPLETED)
    total_expense = Expense.objects.filter(
        q_filter_expense
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_purchase = PurchaseOrder.objects.filter(
        q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_pengeluaran = total_expense + total_purchase
    
    # Laba Bersih
    laba_bersih = total_pemasukan - total_pengeluaran

    # Persentase Perubahan (vs Bulan Lalu) - Ini agak rumit
    # Kita HANYA hitung ini jika periode-nya 'bulan_ini'
    laba_bersih_bulan_lalu = Decimal('0.00')
    persentase_perubahan = 0
    
    if periode == 'bulan_ini':
        # Tentukan rentang tanggal bulan lalu
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        q_filter_transaksi_lm = Q(transaction_date__date__range=(first_day_last_month, last_day_last_month))
        q_filter_expense_lm = Q(date__range=(first_day_last_month, last_day_last_month))
        q_filter_purchase_lm = Q(order_date__date__range=(first_day_last_month, last_day_last_month))

        # Hitung laba bulan lalu
        pemasukan_lm = Transaction.objects.filter(q_filter_transaksi_lm, status=Transaction.StatusChoices.PAID).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        expense_lm = Expense.objects.filter(q_filter_expense_lm).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        purchase_lm = PurchaseOrder.objects.filter(q_filter_purchase_lm, status=PurchaseOrder.StatusChoices.COMPLETED).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        laba_bersih_bulan_lalu = pemasukan_lm - (expense_lm + purchase_lm)

        # Hitung persentase (hindari ZeroDivisionError)
        if laba_bersih_bulan_lalu != Decimal('0.00'):
            persentase_perubahan = ((laba_bersih - laba_bersih_bulan_lalu) / abs(laba_bersih_bulan_lalu)) * 100
        elif laba_bersih > 0:
            persentase_perubahan = 100 # Dari 0 ke > 0
            
    # --- 3. Data Grafik Tren (Line Chart) ---
    
    # Kita akan siapkan data harian jika rentang waktunya ada
    tren_pemasukan_data = {}
    tren_pengeluaran_data = {}
    
    if start_date:
        # Pemasukan harian
        pemasukan_harian = Transaction.objects.filter(
            q_filter_transaksi, status=Transaction.StatusChoices.PAID
        ).annotate(
            day=TruncDay('transaction_date')
        ).values('day').annotate(
            total=Sum('total_amount')
        ).order_by('day')
        
        # Pengeluaran harian (Expense)
        expense_harian = Expense.objects.filter(
            q_filter_expense
        ).annotate(
            day=TruncDay('date')
        ).values('day').annotate(
            total=Sum('amount')
        ).order_by('day')
        
        # Pengeluaran harian (Purchase)
        purchase_harian = PurchaseOrder.objects.filter(
            q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED
        ).annotate(
            day=TruncDay('order_date')
        ).values('day').annotate(
            total=Sum('total_amount')
        ).order_by('day')

        # Gabungkan data untuk Chart.js
        # 1. Buat map untuk pengeluaran
        pengeluaran_map = {}
        for item in expense_harian:
            day_str = item['day'].strftime('%Y-%m-%d')
            pengeluaran_map[day_str] = item['total']
        for item in purchase_harian:
            day_str = item['day'].strftime('%Y-%m-%d')
            pengeluaran_map[day_str] = pengeluaran_map.get(day_str, Decimal('0.00')) + item['total']
            
        # 2. Buat map untuk pemasukan
        pemasukan_map = {}
        for item in pemasukan_harian:
            day_str = item['day'].strftime('%Y-%m-%d')
            pemasukan_map[day_str] = item['total']

        # 3. Dapatkan semua label hari unik
        all_days = sorted(list(set(pemasukan_map.keys()) | set(pengeluaran_map.keys())))
        
        tren_labels = all_days
        tren_pemasukan_data = [float(pemasukan_map.get(day, 0)) for day in all_days]
        tren_pengeluaran_data = [float(pengeluaran_map.get(day, 0)) for day in all_days]

    # --- 4. Distribusi Kategori (Donut Charts) ---

    # Pemasukan: Jasa vs Barang
    # Perlu ekspresi subtotal dari modelmu
    subtotal_item_expr = F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100'))
    subtotal_service_expr = F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100'))

    total_pemasukan_barang = TransactionItem.objects.filter(
        transaction__status=Transaction.StatusChoices.PAID,
        transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).aggregate(total=Sum(subtotal_item_expr))['total'] or Decimal('0.00')

    total_pemasukan_jasa = TransactionService.objects.filter(
        transaction__status=Transaction.StatusChoices.PAID,
        transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).aggregate(total=Sum(subtotal_service_expr))['total'] or Decimal('0.00')

    dist_pemasukan_labels = ['Penjualan Jasa', 'Penjualan Barang']
    dist_pemasukan_data = [float(total_pemasukan_jasa), float(total_pemasukan_barang)]

    # Pengeluaran: Kategori (Expense) vs Vendor (Purchase)
    dist_expense = Expense.objects.filter(q_filter_expense).values('category__name').annotate(
        total=Sum('amount')
    ).order_by('-total')
    
    dist_purchase = PurchaseOrder.objects.filter(q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED).values('vendor__name').annotate(
        total=Sum('total_amount')
    ).order_by('-total')
    
    # Gabungkan
    dist_pengeluaran_labels = [item['category__name'] for item in dist_expense] + \
                              [f"Vendor: {item['vendor__name']}" for item in dist_purchase]
    dist_pengeluaran_data = [float(item['total']) for item in dist_expense] + \
                            [float(item['total']) for item in dist_purchase]


    # --- 5. Top 5 Section ---

    top_montir = Mechanic.objects.filter(
        transaction__status=Transaction.StatusChoices.PAID,
        transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).annotate(
        total_transaksi=Count('transaction')
    ).order_by('-total_transaksi')[:5]

    top_pelanggan = Customer.objects.filter(
        transaction__status=Transaction.StatusChoices.PAID,
        transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).annotate(
        total_belanja=Sum('transaction__total_amount')
    ).order_by('-total_belanja')[:5]

    top_barang = InventoryItem.objects.filter(
        transactionitem__transaction__status=Transaction.StatusChoices.PAID,
        transactionitem__transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).annotate(
        total_terjual=Sum('transactionitem__quantity')
    ).order_by('-total_terjual')[:5]

    top_service = Service.objects.filter(
        transactionservice__transaction__status=Transaction.StatusChoices.PAID,
        transactionservice__transaction__transaction_date__date__range=(start_date, end_date) if start_date else Q()
    ).annotate(
        total_digunakan=Sum('transactionservice__quantity')
    ).order_by('-total_digunakan')[:5]
    
    top_vendor = Vendor.objects.filter(
        purchaseorder__status=PurchaseOrder.StatusChoices.COMPLETED,
        purchaseorder__order_date__date__range=(start_date, end_date) if start_date else Q()
    ).annotate(
        total_pembelian=Sum('purchaseorder__total_amount')
    ).order_by('-total_pembelian')[:5]
    
    # Data untuk chart Top 5 (labels & data)
    top_charts_data = {
        'montir': {
            'labels': [m.name for m in top_montir],
            'data': [m.total_transaksi for m in top_montir],
        },
        'pelanggan': {
            'labels': [p.name for p in top_pelanggan],
            'data': [float(p.total_belanja) for p in top_pelanggan],
        },
        'barang': {
            'labels': [b.name for b in top_barang],
            'data': [b.total_terjual for b in top_barang],
        },
        'service': {
            'labels': [s.name for s in top_service],
            'data': [s.total_digunakan for s in top_service],
        },
        'vendor': {
            'labels': [v.name for v in top_vendor],
            'data': [float(v.total_pembelian) for v in top_vendor],
        }
    }

    # --- 6. Insight Otomatis ---
    insight_text = ""
    try:
        top_pemasukan_sumber = top_service.first()
        top_pengeluaran_sumber = dist_expense.first()
        
        if top_pemasukan_sumber:
            insight_text += f"Pemasukan tertinggi periode ini berasal dari '{top_pemasukan_sumber.name}'."
        if top_pengeluaran_sumber:
             insight_text += f" Pengeluaran operasional terbesar adalah untuk '{top_pengeluaran_sumber['category__name']}'."
    except Exception:
        insight_text = "Data belum cukup untuk menghasilkan insight."


    # --- 7. Kirim data ke Template ---
    
    context = {
        'total_pemasukan': total_pemasukan,
        'total_pengeluaran': total_pengeluaran,
        'laba_bersih': laba_bersih,
        'persentase_perubahan': persentase_perubahan,
        
        # Data untuk JSON di template
        'tren_labels_json': json.dumps(tren_labels) if start_date else json.dumps([]),
        'tren_pemasukan_data_json': json.dumps(tren_pemasukan_data) if start_date else json.dumps([]),
        'tren_pengeluaran_data_json': json.dumps(tren_pengeluaran_data) if start_date else json.dumps([]),
        
        'dist_pemasukan_labels_json': json.dumps(dist_pemasukan_labels),
        'dist_pemasukan_data_json': json.dumps(dist_pemasukan_data),
        
        'dist_pengeluaran_labels_json': json.dumps(dist_pengeluaran_labels),
        'dist_pengeluaran_data_json': json.dumps(dist_pengeluaran_data),
        
        'top_charts_data_json': json.dumps(top_charts_data),
        
        'insight_text': insight_text,
        
        # Untuk state filter
        'current_periode': periode,
        'current_start_date': custom_start or '',
        'current_end_date': custom_end or '',
    }
    
    return render(request, 'dashboard/dashboard.html', context)