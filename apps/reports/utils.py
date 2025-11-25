# apps/reports/utils.py

from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Max, Avg
from django.utils import timezone
from datetime import datetime

# Import Models
from apps.transactions.models import Transaction
from apps.purchases.models import PurchaseOrder
from apps.inventory.models import InventoryItem
from apps.master_data.models import Mechanic, Customer
from apps.expenses.models import Expense

def generate_financial_report(start_date, end_date):
    """
    Menghitung Laba Rugi yang Akurat.
    Rumus: Laba Bersih = Pendapatan - (HPP Pembelian + Beban Operasional)
    """
    # 1. PENDAPATAN (Revenue)
    income_data = Transaction.objects.filter(
        status=Transaction.StatusChoices.COMPLETED,
        created_at__date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))
    
    total_income = income_data['total'] or Decimal('0.00')

    # 2. PENGELUARAN PEMBELIAN (COGS/HPP)
    purchases_data = PurchaseOrder.objects.filter(
        status=PurchaseOrder.StatusChoices.COMPLETED,
        order_date__date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))
    
    total_purchases = purchases_data['total'] or Decimal('0.00')

    # 3. BEBAN OPERASIONAL (Opex)
    expenses_data = Expense.objects.filter(
        date__range=(start_date, end_date)
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
        'total_purchases': total_purchases,
        'total_operational': total_operational_expenses,
        'total_expenses': total_expenses_all,
        'net_profit': net_profit,
    }

def generate_low_stock_report():
    low_stock_items = InventoryItem.objects.filter(
        quantity__lte=F('reorder_threshold')
    ).annotate(
        asset_value=F('quantity') * F('buy_price')
    ).order_by('quantity')
    return low_stock_items

def generate_mechanic_performance_report(mechanic_id, start_date, end_date):
    """
    Analisis Kinerja Mekanik termasuk Rata-rata Durasi Pengerjaan.
    """
    try:
        mechanic = Mechanic.objects.get(pk=mechanic_id)
    except Mechanic.DoesNotExist:
        return None

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
    date_filter = Q(
        vehicles__transaction__status=Transaction.StatusChoices.COMPLETED,
        vehicles__transaction__created_at__date__range=(start_date, end_date)
    )

    customers = Customer.objects.annotate(
        total_visits=Count('vehicles__transaction', filter=date_filter),
        total_spending=Sum('vehicles__transaction__total_amount', filter=date_filter),
        last_visit=Max('vehicles__transaction__created_at', filter=date_filter)
    ).filter(
        total_visits__gt=0
    ).order_by(sort_by)

    return customers