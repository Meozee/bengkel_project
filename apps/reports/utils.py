# apps/reports/utils.py
from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Max, Avg
from django.utils import timezone
from datetime import datetime

# Import Models
from apps.transactions.models import Transaction, TransactionItem 
from apps.purchases.models import PurchaseOrder
from apps.inventory.models import InventoryItem
from apps.master_data.models import Mechanic, Customer
from apps.expenses.models import Expense


from datetime import datetime, timedelta # <--- TAMBAHKAN timedelta



def generate_financial_report(start_date, end_date):
    """
    Menghitung Laba Rugi yang Akurat.
    Rumus: Laba Bersih = Pendapatan - (HPP Pembelian + Beban Operasional)
    """
    # 1. PENDAPATAN (Revenue)
    # Hanya hitung transaksi yang sudah COMPLETED (uang masuk)
    income_data = Transaction.objects.filter(
        status=Transaction.StatusChoices.COMPLETED,
        created_at__date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))
    
    total_income = income_data['total'] or Decimal('0.00')

    # 2. PENGELUARAN PEMBELIAN (COGS/HPP)
    # Uang yang dipakai untuk beli stok barang (Restock)
    purchases_data = PurchaseOrder.objects.filter(
        status=PurchaseOrder.StatusChoices.COMPLETED,
        order_date__date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))
    
    total_purchases = purchases_data['total'] or Decimal('0.00')

    # 3. BEBAN OPERASIONAL (Opex)
    # Listrik, Gaji, Air, Sewa, dll (Hanya yang status PAID)
    expenses_data = Expense.objects.filter(
        status=Expense.StatusChoices.PAID,
        payment_date__range=(start_date, end_date)
    ).aggregate(total=Sum('amount'))
    
    total_operational_expenses = expenses_data['total'] or Decimal('0.00')

    # 4. TOTAL PENGELUARAN (Gabungan)
    total_expenses_all = total_purchases + total_operational_expenses

    # 5. LABA BERSIH (Net Profit)
    net_profit = total_income - total_expenses_all

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_purchases': total_purchases, # Breakdown Pembelian
        'total_operational': total_operational_expenses, # Breakdown Operasional
        'total_expenses': total_expenses_all,
        'net_profit': net_profit,
    }

def generate_low_stock_report():
    """
    Laporan Inventory: Item stok rendah & Nilai Aset.
    """
    # Ambil item yang qty <= threshold
    low_stock_items = InventoryItem.objects.filter(
        quantity__lte=F('reorder_threshold')
    ).annotate(
        asset_value=F('quantity') * F('buy_price') # Hitung nilai aset tersisa
    ).order_by('quantity')
    
    return low_stock_items

def generate_mechanic_performance_report(mechanic_id, start_date, end_date):
    """
    Analisis Kinerja Mekanik (Status COMPLETED) + Rata-rata Kecepatan.
    """
    try:
        mechanic = Mechanic.objects.get(pk=mechanic_id)
    except Mechanic.DoesNotExist:
        return None

    # Filter hanya transaksi COMPLETED
    transactions = Transaction.objects.filter(
        mechanic=mechanic,
        status=Transaction.StatusChoices.COMPLETED,
        created_at__date__range=(start_date, end_date)
    )

    performance_data = transactions.aggregate(
        total_jobs=Count('id'),
        total_revenue=Sum('total_amount')
    )

    # --- HITUNG AVG DURATION ---
    # Hitung selisih (completed_at - created_at)
    avg_duration_qs = transactions.filter(
        completed_at__isnull=False
    ).aggregate(
        avg_time=Avg(F('completed_at') - F('created_at'))
    )
    
    avg_duration = avg_duration_qs['avg_time'] # Returns timedelta or None

    # Format ke string "X jam Y menit"
    avg_duration_str = "-"
    if avg_duration:
        total_seconds = int(avg_duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        if hours > 0:
            avg_duration_str = f"{hours} jam {minutes} menit"
        else:
            avg_duration_str = f"{minutes} menit"

    # Cari jasa apa yang paling sering dia kerjakan
    top_service = transactions.values('services__service__name').annotate(
        service_count=Count('services__service')
    ).order_by('-service_count').first()

    return {
        'mechanic': mechanic,
        'start_date': start_date,
        'end_date': end_date,
        'total_jobs': performance_data['total_jobs'] or 0,
        'total_revenue': performance_data['total_revenue'] or Decimal('0.00'),
        'avg_duration_str': avg_duration_str, # Data Baru
        'top_service': top_service['services__service__name'] if top_service else "Belum ada data",
        'top_service_count': top_service['service_count'] if top_service else 0,
    }

def generate_customer_report(start_date, end_date, sort_by='-total_spending'):
    """
    Analisis Pelanggan (Status COMPLETED).
    """
    # Filter transaksi valid dalam range tanggal
    date_filter = Q(
        vehicles__transaction__status=Transaction.StatusChoices.COMPLETED,
        vehicles__transaction__created_at__date__range=(start_date, end_date)
    )

    customers = Customer.objects.annotate(
        total_visits=Count('vehicles__transaction', filter=date_filter),
        total_spending=Sum('vehicles__transaction__total_amount', filter=date_filter),
        last_visit=Max('vehicles__transaction__created_at', filter=date_filter)
    ).filter(
        total_visits__gt=0 # Hanya ambil customer yang pernah transaksi di periode ini
    ).order_by(sort_by)

    return customers

    # === 1. EXPENSE BREAKDOWN REPORT ===
def generate_expense_breakdown(start_date, end_date):
    """
    Rincian pengeluaran berdasarkan kategori.
    Hanya menghitung status PAID.
    """
    expenses = Expense.objects.filter(
        status=Expense.StatusChoices.PAID,
        payment_date__range=(start_date, end_date)
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')

    total_expense = expenses.aggregate(sum=Sum('total'))['sum'] or Decimal('0.00')

    # Tambahkan persentase
    breakdown = []
    for item in expenses:
        percent = (item['total'] / total_expense * 100) if total_expense > 0 else 0
        breakdown.append({
            'category': item['category__name'],
            'total': item['total'],
            'count': item['count'],
            'percent': round(percent, 1)
        })

    return {
        'start_date': start_date,
        'end_date': end_date,
        'breakdown': breakdown,
        'total_expense': total_expense
    }

# === 2. DEAD STOCK REPORT ===
def generate_dead_stock_report(days_threshold=90):
    """
    Mencari barang yang STOKNYA ADA (>0) tapi TIDAK ADA PENJUALAN dalam X hari terakhir.
    """
    cutoff_date = timezone.now() - timedelta(days=int(days_threshold))
    
    # Ambil item yang punya stok
    items = InventoryItem.objects.filter(quantity__gt=0)
    
    dead_stock = []
    for item in items:
        # Cek kapan terakhir terjual (Completed Transaction)
        last_sale = TransactionItem.objects.filter(
            item=item,
            transaction__status=Transaction.StatusChoices.COMPLETED
        ).aggregate(last_date=Max('transaction__created_at'))['last_date']

        # Jika tidak pernah terjual ATAU terakhir terjual sebelum cutoff date
        if last_sale is None or last_sale < cutoff_date:
            dead_stock.append({
                'item': item,
                'last_sale': last_sale,
                'days_inactive': (timezone.now() - last_sale).days if last_sale else "Selamanya",
                'asset_value': item.quantity * item.buy_price
            })
    
    # Sort by nilai aset tertinggi (uang mandeg terbanyak)
    dead_stock.sort(key=lambda x: x['asset_value'], reverse=True)
    
    return dead_stock

# === 3. SALES REPORT ===
def generate_sales_report(start_date, end_date):
    """
    Rincian penjualan per barang (Item Sales).
    """
    sales = TransactionItem.objects.filter(
        transaction__status=Transaction.StatusChoices.COMPLETED,
        transaction__created_at__date__range=(start_date, end_date)
    ).values(
        'item__name', 'item__sku', 'item__buy_price'
    ).annotate(
        total_qty=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('unit_price') * (Decimal('1') - F('discount_percentage') / Decimal('100')))
    ).order_by('-total_revenue')

    # Hitung Estimasi Profit (Revenue - HPP)
    # Note: Ini estimasi kasar menggunakan buy_price saat ini
    sales_data = []
    total_omzet = Decimal('0.00')
    total_profit = Decimal('0.00')

    for s in sales:
        hpp = s['total_qty'] * s['item__buy_price']
        profit = s['total_revenue'] - hpp
        
        total_omzet += s['total_revenue']
        total_profit += profit

        sales_data.append({
            'name': s['item__name'],
            'sku': s['item__sku'],
            'qty': s['total_qty'],
            'revenue': s['total_revenue'],
            'hpp_total': hpp,
            'profit': profit,
            'margin': (profit / s['total_revenue'] * 100) if s['total_revenue'] > 0 else 0
        })

    return {
        'start_date': start_date,
        'end_date': end_date,
        'sales_data': sales_data,
        'total_omzet': total_omzet,
        'total_profit': total_profit
    }