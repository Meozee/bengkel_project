from decimal import Decimal
from django.db.models import Sum, Count, Q, F, Max
from django.utils import timezone
from datetime import datetime

from apps.transactions.models import Transaction
from apps.purchases.models import PurchaseOrder
from apps.inventory.models import InventoryItem
from apps.master_data.models import Mechanic, Customer

def generate_financial_report(start_date, end_date):
    """
    Menghitung pendapatan, pengeluaran, dan laba bersih dalam rentang tanggal.
    """
    # --- PENDAPATAN ---
    income_from_transactions = Transaction.objects.filter(
        status='PAID',
        transaction_date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')

    total_income = income_from_transactions

    # --- PENGELUARAN ---
    expenses_from_purchases = PurchaseOrder.objects.filter(
        status='COMPLETED',
        order_date__range=(start_date, end_date)
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0.00')
    
    total_expenses = expenses_from_purchases

    # --- LABA BERSIH ---
    net_profit = total_income - total_expenses

    return {
        'start_date': start_date,
        'end_date': end_date,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_profit': net_profit,
    }

def generate_low_stock_report():
    """
    Mengambil semua item inventaris yang stoknya di bawah atau sama dengan ambang batas.
    """
    low_stock_items = InventoryItem.objects.filter(
        quantity__lte=F('reorder_threshold')
    ).order_by('quantity')
    
    return low_stock_items

def generate_mechanic_performance_report(mechanic_id, start_date, end_date):
    """
    Menganalisis kinerja seorang mekanik dalam rentang tanggal.
    """
    try:
        mechanic = Mechanic.objects.get(pk=mechanic_id)
    except Mechanic.DoesNotExist:
        return None

    transactions = Transaction.objects.filter(
        mechanic=mechanic,
        status='PAID',
        transaction_date__range=(start_date, end_date)
    )

    performance_data = transactions.aggregate(
        total_jobs=Count('id'),
        total_revenue=Sum('total_amount')
    )

    top_service = transactions.values('services__service__name').annotate(
        service_count=Count('services__service')
    ).order_by('-service_count').first()

    return {
        'mechanic': mechanic,
        'start_date': start_date,
        'end_date': end_date,
        'total_jobs': performance_data['total_jobs'] or 0,
        'total_revenue': performance_data['total_revenue'] or Decimal('0.00'),
        'top_service': top_service['services__service__name'] if top_service else "N/A",
        'top_service_count': top_service['service_count'] if top_service else 0,
    }

def generate_customer_report(start_date, end_date, sort_by='-total_spending'):
    """
    Menganalisis data pelanggan berdasarkan transaksi dalam rentang tanggal.
    """
    date_filter = Q(
        vehicles__transaction__status='PAID',
        vehicles__transaction__transaction_date__range=(start_date, end_date)
    )

    customers = Customer.objects.annotate(
        total_visits=Count('vehicles__transaction', filter=date_filter),
        total_spending=Sum('vehicles__transaction__total_amount', filter=date_filter),
        last_visit=Max('vehicles__transaction__transaction_date', filter=date_filter)
    ).filter(
        total_visits__gt=0
    ).order_by(sort_by)

    return customers