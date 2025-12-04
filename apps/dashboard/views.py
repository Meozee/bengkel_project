# apps/dashboard/views.py

import json
from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta 

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Sum, Count, F, Q, Avg
from django.db.models.functions import TruncDay, TruncMonth

# Import models
from apps.transactions.models import Transaction, TransactionItem, TransactionService
from apps.expenses.models import Expense
from apps.purchases.models import PurchaseOrder
from apps.master_data.models import Mechanic, Customer, Service, Vendor
from apps.inventory.models import InventoryItem

@login_required
def dashboard_view(request):
    
    # --- 1. Logika Filter Tanggal ---
    periode = request.GET.get('periode', 'bulan_ini')
    custom_start = request.GET.get('start_date')
    custom_end = request.GET.get('end_date')

    today = timezone.now().date()
    
    if periode == 'bulan_ini':
        start_date = today.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)
    elif periode == 'bulan_lalu':
        first_day_current_month = today.replace(day=1)
        end_date = first_day_current_month - timedelta(days=1)
        start_date = end_date.replace(day=1)
    elif periode == 'custom' and custom_start and custom_end:
        start_date = custom_start
        end_date = custom_end
    else: 
        periode = 'keseluruhan'
        start_date = None
        end_date = None

    # Q Objects dasar untuk filter
    q_filter_transaksi = Q(created_at__date__range=(start_date, end_date)) if start_date else Q()
    q_filter_purchase = Q(order_date__date__range=(start_date, end_date)) if start_date else Q()
    q_filter_expense = Q(payment_date__range=(start_date, end_date)) if start_date else Q()

    # --- 2. Perhitungan KPI ---
    total_pemasukan = Transaction.objects.filter(
        q_filter_transaksi, status=Transaction.StatusChoices.COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_expense = Expense.objects.filter(
        q_filter_expense, status=Expense.StatusChoices.PAID
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_purchase = PurchaseOrder.objects.filter(
        q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_pengeluaran = total_expense + total_purchase
    laba_bersih = total_pemasukan - total_pengeluaran

    # Persentase Perubahan
    laba_bersih_bulan_lalu = Decimal('0.00')
    persentase_perubahan = 0
    
    if periode == 'bulan_ini':
        first_day_current_month = today.replace(day=1)
        last_day_last_month = first_day_current_month - timedelta(days=1)
        first_day_last_month = last_day_last_month.replace(day=1)
        
        q_filter_transaksi_lm = Q(created_at__date__range=(first_day_last_month, last_day_last_month))
        q_filter_expense_lm = Q(payment_date__range=(first_day_last_month, last_day_last_month))
        q_filter_purchase_lm = Q(order_date__date__range=(first_day_last_month, last_day_last_month))

        pemasukan_lm = Transaction.objects.filter(q_filter_transaksi_lm, status=Transaction.StatusChoices.COMPLETED).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        expense_lm = Expense.objects.filter(q_filter_expense_lm, status=Expense.StatusChoices.PAID).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        purchase_lm = PurchaseOrder.objects.filter(q_filter_purchase_lm, status=PurchaseOrder.StatusChoices.COMPLETED).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
        
        laba_bersih_bulan_lalu = pemasukan_lm - (expense_lm + purchase_lm)

        if laba_bersih_bulan_lalu != Decimal('0.00'):
            persentase_perubahan = ((laba_bersih - laba_bersih_bulan_lalu) / abs(laba_bersih_bulan_lalu)) * 100
        elif laba_bersih > 0:
            persentase_perubahan = 100
            
    # --- 3. Data Grafik Tren ---
    tren_labels = []
    tren_pemasukan_data = []
    tren_pengeluaran_data = []
    
    if start_date:
        date_format = '%Y-%m-%d'
        pemasukan_harian = Transaction.objects.filter(q_filter_transaksi, status=Transaction.StatusChoices.COMPLETED).annotate(day=TruncDay('created_at')).values('day').annotate(total=Sum('total_amount')).order_by('day')
        expense_harian = Expense.objects.filter(q_filter_expense, status=Expense.StatusChoices.PAID).annotate(day=TruncDay('payment_date')).values('day').annotate(total=Sum('amount')).order_by('day')
        purchase_harian = PurchaseOrder.objects.filter(q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED).annotate(day=TruncDay('order_date')).values('day').annotate(total=Sum('total_amount')).order_by('day')

        pengeluaran_map = {}
        for item in expense_harian: pengeluaran_map[item['day'].strftime(date_format)] = item['total']
        for item in purchase_harian: 
            key = item['day'].strftime(date_format)
            pengeluaran_map[key] = pengeluaran_map.get(key, Decimal('0.00')) + item['total']
        
        pemasukan_map = {}
        for item in pemasukan_harian: pemasukan_map[item['day'].strftime(date_format)] = item['total']

        all_days = sorted(list(set(pemasukan_map.keys()) | set(pengeluaran_map.keys())))
        tren_labels = all_days
        tren_pemasukan_data = [float(pemasukan_map.get(day, 0)) for day in all_days]
        tren_pengeluaran_data = [float(pengeluaran_map.get(day, 0)) for day in all_days]

    else:
        date_format = '%Y-%m'
        
        # Tambahkan .exclude(created_at__isnull=True)
        pemasukan_bulanan = Transaction.objects.filter(
            q_filter_transaksi, 
            status=Transaction.StatusChoices.COMPLETED
        ).exclude(created_at__isnull=True).annotate( # <-- SAFETY
            month=TruncMonth('created_at')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')

        # Tambahkan .exclude(payment_date__isnull=True)
        expense_bulanan = Expense.objects.filter(
            q_filter_expense, 
            status=Expense.StatusChoices.PAID
        ).exclude(payment_date__isnull=True).annotate( # <-- SAFETY (INI YANG BIKIN ERROR TADI)
            month=TruncMonth('payment_date')
        ).values('month').annotate(
            total=Sum('amount')
        ).order_by('month')

        # Tambahkan .exclude(order_date__isnull=True)
        purchase_bulanan = PurchaseOrder.objects.filter(
            q_filter_purchase, 
            status=PurchaseOrder.StatusChoices.COMPLETED
        ).exclude(order_date__isnull=True).annotate( # <-- SAFETY
            month=TruncMonth('order_date')
        ).values('month').annotate(
            total=Sum('total_amount')
        ).order_by('month')

        pengeluaran_map = {}
        for item in expense_bulanan: pengeluaran_map[item['month'].strftime(date_format)] = item['total']
        for item in purchase_bulanan: 
            key = item['month'].strftime(date_format)
            pengeluaran_map[key] = pengeluaran_map.get(key, Decimal('0.00')) + item['total']
        
        pemasukan_map = {}
        for item in pemasukan_bulanan: pemasukan_map[item['month'].strftime(date_format)] = item['total']

        all_months = sorted(list(set(pemasukan_map.keys()) | set(pengeluaran_map.keys())))
        tren_labels = all_months
        tren_pemasukan_data = [float(pemasukan_map.get(month, 0)) for month in all_months]
        tren_pengeluaran_data = [float(pengeluaran_map.get(month, 0)) for month in all_months]


    # --- 4. Distribusi Kategori ---
    subtotal_item_expr = F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100'))
    subtotal_service_expr = F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100'))

    total_pemasukan_barang = TransactionItem.objects.filter(
        transaction__status=Transaction.StatusChoices.COMPLETED,
        transaction__created_at__date__range=(start_date, end_date) if start_date else Q()
    ).aggregate(total=Sum(subtotal_item_expr))['total'] or Decimal('0.00')

    total_pemasukan_jasa = TransactionService.objects.filter(
        transaction__status=Transaction.StatusChoices.COMPLETED,
        transaction__created_at__date__range=(start_date, end_date) if start_date else Q()
    ).aggregate(total=Sum(subtotal_service_expr))['total'] or Decimal('0.00')

    dist_pemasukan_labels = ['Penjualan Jasa', 'Penjualan Barang']
    dist_pemasukan_data = [float(total_pemasukan_jasa), float(total_pemasukan_barang)]

    dist_expense = Expense.objects.filter(
        q_filter_expense, status=Expense.StatusChoices.PAID
    ).values('category__name').annotate(total=Sum('amount')).order_by('-total')
    
    dist_purchase = PurchaseOrder.objects.filter(
        q_filter_purchase, status=PurchaseOrder.StatusChoices.COMPLETED
    ).values('vendor__name').annotate(total=Sum('total_amount')).order_by('-total')
    
    dist_pengeluaran_labels = [item['category__name'] for item in dist_expense] + [f"Vendor: {item['vendor__name']}" for item in dist_purchase]
    dist_pengeluaran_data = [float(item['total']) for item in dist_expense] + [float(item['total']) for item in dist_purchase]


    # --- 5. Top 5 Section ---

    # Filter Umum untuk Transaksi
    top_filter = Q(transaction__status=Transaction.StatusChoices.COMPLETED)
    if start_date:
        top_filter &= Q(transaction__created_at__date__range=(start_date, end_date))

    # 1. Top Montir (Jumlah Job)
    top_montir = Mechanic.objects.filter(top_filter).annotate(total_transaksi=Count('transaction')).order_by('-total_transaksi')[:5]
    
    # 2. Top Montir (Kecepatan)
    top_montir_speed = Mechanic.objects.filter(
        top_filter, transaction__completed_at__isnull=False
    ).annotate(
        avg_duration=Avg(F('transaction__completed_at') - F('transaction__created_at'))
    ).order_by('avg_duration')[:5]

    speed_labels = []
    speed_data = []
    for m in top_montir_speed:
        if m.avg_duration:
            minutes = m.avg_duration.total_seconds() / 60
            speed_labels.append(m.name)
            speed_data.append(round(minutes, 1))

    # 3. Top Pelanggan
    top_pelanggan = Customer.objects.filter(top_filter).annotate(total_belanja=Sum('transaction__total_amount')).order_by('-total_belanja')[:5]
    
    # 4. Top Barang
    item_filter = Q(transactionitem__transaction__status=Transaction.StatusChoices.COMPLETED)
    if start_date: item_filter &= Q(transactionitem__transaction__created_at__date__range=(start_date, end_date))
    top_barang = InventoryItem.objects.filter(item_filter).annotate(total_terjual=Sum('transactionitem__quantity')).order_by('-total_terjual')[:5]

    # 5. Top Service
    svc_filter = Q(transactionservice__transaction__status=Transaction.StatusChoices.COMPLETED)
    if start_date: svc_filter &= Q(transactionservice__transaction__created_at__date__range=(start_date, end_date))
    top_service = Service.objects.filter(svc_filter).annotate(total_digunakan=Sum('transactionservice__quantity')).order_by('-total_digunakan')[:5]
    
    # 6. Top Vendor (PERBAIKAN ERROR DI SINI)
    # Kita buat filter khusus untuk Vendor karena dia relasinya ke PurchaseOrder
    vendor_filter = Q(purchaseorder__status=PurchaseOrder.StatusChoices.COMPLETED)
    if start_date:
        # Gunakan purchaseorder__order_date untuk filter vendor
        vendor_filter &= Q(purchaseorder__order_date__date__range=(start_date, end_date))

    top_vendor = Vendor.objects.filter(vendor_filter).annotate(
        total_pembelian=Sum('purchaseorder__total_amount')
    ).order_by('-total_pembelian')[:5]
    
    # Bundle Data
    top_charts_data = {
        'montir': {'labels': [m.name for m in top_montir], 'data': [m.total_transaksi for m in top_montir]},
        'montir_speed': {'labels': speed_labels, 'data': speed_data}, 
        'pelanggan': {'labels': [p.name for p in top_pelanggan], 'data': [float(p.total_belanja) for p in top_pelanggan]},
        'barang': {'labels': [b.name for b in top_barang], 'data': [b.total_terjual for b in top_barang]},
        'service': {'labels': [s.name for s in top_service], 'data': [s.total_digunakan for s in top_service]},
        'vendor': {'labels': [v.name for v in top_vendor], 'data': [float(v.total_pembelian) for v in top_vendor]}
    }

    # --- 6. Insight ---
    insight_text = ""
    try:
        top_income = top_service.first()
        if top_income: insight_text += f"Pemasukan tertinggi dari '{top_income.name}'."
        if speed_labels: insight_text += f" Montir tercepat periode ini adalah '{speed_labels[0]}'."
    except:
        insight_text = "Data belum cukup."


    context = {
        'total_pemasukan': total_pemasukan,
        'total_pengeluaran': total_pengeluaran,
        'laba_bersih': laba_bersih,
        'persentase_perubahan': persentase_perubahan,
        
        'tren_labels_json': json.dumps(tren_labels),
        'tren_pemasukan_data_json': json.dumps(tren_pemasukan_data),
        'tren_pengeluaran_data_json': json.dumps(tren_pengeluaran_data),
        'dist_pemasukan_labels_json': json.dumps(dist_pemasukan_labels),
        'dist_pemasukan_data_json': json.dumps(dist_pemasukan_data),
        'dist_pengeluaran_labels_json': json.dumps(dist_pengeluaran_labels),
        'dist_pengeluaran_data_json': json.dumps(dist_pengeluaran_data),
        
        'top_charts_data_json': json.dumps(top_charts_data),
        'insight_text': insight_text,
        
        'current_periode': periode,
        'current_start_date': custom_start or '',
        'current_end_date': custom_end or '',
    }
    
    return render(request, 'dashboard/dashboard.html', context)