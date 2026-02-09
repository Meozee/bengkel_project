from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Max, Avg, Min, Case, When, Value, CharField
from django.db.models.functions import Coalesce, Concat
from django.utils import timezone
from datetime import datetime, timedelta

# Import Models
from apps.transactions.models import Transaction, TransactionItem, TransactionService
from apps.purchases.models import PurchaseOrder
from apps.inventory.models import InventoryItem, VehicleServicePrice
from apps.master_data.models import Mechanic, Customer, Vehicle
from apps.expenses.models import Expense, ExpenseCategory

# ==============================================================================
# 1. LAPORAN KEUANGAN (PROFIT & LOSS)
# ==============================================================================
def generate_financial_report(start_date, end_date):
    """
    Menghitung Laba Rugi Sederhana.
    """
    # A. PENDAPATAN (Revenue) - Transaksi COMPLETED
    transactions = Transaction.objects.filter(
        status=Transaction.StatusChoices.COMPLETED,
        created_at__date__range=(start_date, end_date)
    )
    income_data = transactions.aggregate(total=Sum('total_amount'))
    total_income = income_data['total'] or Decimal('0.00')

    # B. BEBAN POKOK (COGS) - Pembelian Sparepart (Restock)
    # Filter PO yang statusnya COMPLETED
    purchases_data = PurchaseOrder.objects.filter(
        status=PurchaseOrder.StatusChoices.COMPLETED,
        order_date__date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))
    total_purchases = purchases_data['total'] or Decimal('0.00')

    # C. BEBAN OPERASIONAL (OPEX) - Gaji, Listrik, dll
    # Filter Expense yang statusnya PAID
    expenses_data = Expense.objects.filter(
        status='PAID',
        payment_date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))
    total_operational = expenses_data['total'] or Decimal('0.00')

    # Total Pengeluaran
    total_expenses = total_purchases + total_operational

    # Net Profit
    net_profit = total_income - total_expenses

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_purchases': total_purchases,
        'total_operational': total_operational,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
    }

# ==============================================================================
# 2. LAPORAN INVENTARIS (FILTER LENGKAP)
# ==============================================================================
def get_inventory_queryset(filters):
    """
    Queryset Inventory dengan Filter Canggih.
    filters: dict dari request.GET
    """
    items = InventoryItem.objects.select_related('category').prefetch_related('service_prices')

    # 1. Filter Search (Nama / SKU)
    q = filters.get('q')
    if q:
        items = items.filter(Q(name__icontains=q) | Q(sku__icontains=q))

    # 2. Filter Kategori
    category_id = filters.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # 3. Filter Status Stok
    stock_status = filters.get('stock_status')
    if stock_status == 'low':
        items = items.filter(quantity__lte=F('reorder_threshold'))
    elif stock_status == 'out':
        items = items.filter(quantity=0)
    elif stock_status == 'safe':
        items = items.filter(quantity__gt=F('reorder_threshold'))

    # 4. Filter Range Harga Jual
    min_price = filters.get('min_price')
    max_price = filters.get('max_price')
    if min_price:
        items = items.filter(sell_price__gte=min_price)
    if max_price:
        items = items.filter(sell_price__lte=max_price)

    # 5. Filter Status Aktif/Arsip
    status = filters.get('status')
    if status == 'archived':
        items = items.filter(is_active=False)
    elif status == 'active': # Default usually active only or all
        items = items.filter(is_active=True)
    
    # 6. Filter Join Date (Created At)
    join_date_start = filters.get('join_date_start')
    join_date_end = filters.get('join_date_end')
    if join_date_start and join_date_end:
        items = items.filter(created_at__date__range=(join_date_start, join_date_end))

    # Annotate Aset Value & Service Price Range (Min - Max)
    items = items.annotate(
        asset_value=F('quantity') * F('buy_price'),
        min_service_price=Min('service_prices__price'),
        max_service_price=Max('service_prices__price')
    ).order_by('-updated_at') # Default sort last update

    return items

# ==============================================================================
# 3. LAPORAN KINERJA MEKANIK (DETAIL & MULTI)
# ==============================================================================
def get_mechanic_performance_data(mechanic_ids, start_date, end_date):
    """
    Mengambil data detail untuk satu atau banyak mekanik.
    mechanic_ids: list of ID string ['1', '2'] atau None (All)
    """
    mechanics = Mechanic.objects.all()
    if mechanic_ids:
        mechanics = mechanics.filter(id__in=mechanic_ids)

    report_data = []

    for mech in mechanics:
        # A. Transaksi yang ditangani (Pendapatan Service)
        txns = Transaction.objects.filter(
            mechanic=mech,
            status=Transaction.StatusChoices.COMPLETED,
            created_at__date__range=(start_date, end_date)
        ).select_related('customer', 'vehicle').prefetch_related('services__service', 'items__item')

        total_jobs = txns.count()
        total_revenue = txns.aggregate(sum=Sum('total_amount'))['sum'] or Decimal('0')

        # B. Pengeluaran oleh Mekanik (Jika ada fitur reimburse/belanja)
        # Asumsi: PurchaseOrder punya field purchaser_mechanic
        purchases = PurchaseOrder.objects.filter(
            purchaser_mechanic=mech,
            status=PurchaseOrder.StatusChoices.COMPLETED,
            order_date__date__range=(start_date, end_date)
        )
        total_expense = purchases.aggregate(sum=Sum('total_amount'))['sum'] or Decimal('0')

        # Detail Jobs untuk Table
        job_details = []
        for t in txns:
            service_names = ", ".join([s.service.name for s in t.services.all()])
            item_names = ", ".join([i.item.name for i in t.items.all()])
            desc = []
            if service_names: desc.append(f"[Jasa] {service_names}")
            if item_names: desc.append(f"[Part] {item_names}")
            
            job_details.append({
                'date': t.created_at,
                'invoice': t.invoice_number,
                'plate': t.vehicle.license_plate if t.vehicle else "Tanpa Kendaraan",
                'description': " + ".join(desc),
                'amount': t.total_amount
            })

        report_data.append({
            'mechanic_name': mech.name,
            'total_jobs': total_jobs,
            'total_revenue': total_revenue,
            'total_expense': total_expense,
            'net_contribution': total_revenue - total_expense,
            'job_details': job_details, # List transaksi detail
            'expense_details': purchases, # Queryset PO
        })

    return report_data

# ==============================================================================
# 4. LAPORAN KENDARAAN (VEHICLE HISTORY)
# ==============================================================================
def get_vehicle_history_queryset(filters):
    """
    Fokus ke Plat Nomor Kendaraan.
    """
    # Base Query: Kendaraan yang pernah transaksi COMPLETED
    vehicles = Vehicle.objects.filter(
        transaction__status=Transaction.StatusChoices.COMPLETED
    ).distinct()

    # Filter Plat Nomor
    plate = filters.get('plate')
    if plate:
        vehicles = vehicles.filter(license_plate__icontains=plate)

    # Annotate Metrics
    vehicles = vehicles.annotate(
        total_visits=Count('transaction', filter=Q(transaction__status='COMPLETED')),
        total_spending=Sum('transaction__total_amount', filter=Q(transaction__status='COMPLETED')),
        last_visit=Max('transaction__created_at', filter=Q(transaction__status='COMPLETED'))
    )

    # Filter Range Kunjungan / Belanja
    min_visits = filters.get('min_visits')
    if min_visits:
        vehicles = vehicles.filter(total_visits__gte=min_visits)
    
    # Sort
    sort_by = filters.get('sort_by', '-last_visit')
    vehicles = vehicles.order_by(sort_by)

    return vehicles

# ==============================================================================
# 5. LAPORAN PENJUALAN BARANG (SALES ANALYSIS)
# ==============================================================================
def get_sales_report_data(filters):
    start_date = filters.get('start_date')
    end_date = filters.get('end_date')
    
    # Base Query: Item Transaksi yang COMPLETED
    sales = TransactionItem.objects.filter(
        transaction__status=Transaction.StatusChoices.COMPLETED,
        transaction__created_at__date__range=(start_date, end_date)
    )

    # Filter Nama Barang / Kategori
    q = filters.get('q')
    if q:
        sales = sales.filter(item__name__icontains=q)
    
    cat = filters.get('category')
    if cat:
        sales = sales.filter(item__category_id=cat)

    # Grouping by Item
    report = sales.values(
        'item__name', 'item__category__name', 'item__sku', 'item__buy_price'
    ).annotate(
        qty_sold=Sum('quantity'),
        # Hitung Revenue Real (Harga jual di transaksi - diskon)
        total_revenue=Sum(F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100')))
    ).order_by('-total_revenue')

    # Post-processing untuk Profit & Margin
    final_data = []
    total_omzet = Decimal(0)
    total_profit = Decimal(0)

    for row in report:
        # HPP Total = Qty Terjual * Harga Beli Master (Estimasi)
        # Note: Untuk akurasi 100% harusnya pakai FIFO di TransactionItemSource, tapi ini cukup untuk report general
        hpp_total = row['qty_sold'] * row['item__buy_price']
        profit = row['total_revenue'] - hpp_total
        margin = (profit / row['total_revenue'] * 100) if row['total_revenue'] > 0 else 0

        total_omzet += row['total_revenue']
        total_profit += profit

        final_data.append({
            'name': row['item__name'],
            'category': row['item__category__name'],
            'qty': row['qty_sold'],
            'revenue': row['total_revenue'],
            'hpp': hpp_total,
            'profit': profit,
            'margin': margin
        })

    return final_data, total_omzet, total_profit

# ==============================================================================
# 6. LAPORAN BARANG MATI (DEAD STOCK)
# ==============================================================================
def get_dead_stock_queryset(days_threshold=90, category_id=None, q=None):
    cutoff_date = timezone.now() - timedelta(days=int(days_threshold))
    
    # Barang yang punya stok > 0
    items = InventoryItem.objects.filter(quantity__gt=0)

    if category_id:
        items = items.filter(category_id=category_id)
    if q:
        items = items.filter(name__icontains=q)

    dead_stock = []
    for item in items:
        # Cari tanggal transaksi terakhir
        last_txn = TransactionItem.objects.filter(
            item=item,
            transaction__status=Transaction.StatusChoices.COMPLETED
        ).aggregate(last_date=Max('transaction__created_at'))['last_date']

        # Jika belum pernah laku ATAU laku terakhir sebelum cutoff
        if last_txn is None or last_txn < cutoff_date:
            days_inactive = (timezone.now() - last_txn).days if last_txn else 9999
            dead_stock.append({
                'item': item,
                'last_sale': last_txn,
                'days_inactive': days_inactive if days_inactive != 9999 else "Belum Pernah",
                'asset_value': item.quantity * item.buy_price
            })
    
    # Sort by Asset Value (Uang Mandeg)
    dead_stock.sort(key=lambda x: x['asset_value'], reverse=True)
    return dead_stock

# ==============================================================================
# 7. RINCIAN PENGELUARAN
# ==============================================================================
def get_expense_queryset(filters):
    expenses = Expense.objects.select_related('category').filter(status='PAID')

    start = filters.get('start_date')
    end = filters.get('end_date')
    if start and end:
        expenses = expenses.filter(payment_date__range=(start, end))
    
    cat = filters.get('category')
    if cat:
        expenses = expenses.filter(category_id=cat)
    
    q = filters.get('q') # Cari nama pengeluaran
    if q:
        expenses = expenses.filter(title__icontains=q)

    return expenses.order_by('-payment_date')