from django.db.models import F
from apps.transactions.models import Transaction
from apps.inventory.models import InventoryItem
from apps.purchases.models import PurchaseOrder
from apps.expenses.models import Expense

def global_notifications(request):
    # Jika user belum login, jangan load apa-apa biar ringan
    if not request.user.is_authenticated:
        return {}

    # 1. Hitung Transaksi Pending
    pending_transactions_count = Transaction.objects.filter(
        status=Transaction.StatusChoices.PENDING
    ).count()

    # 2. Hitung Low Stock (Stok <= Ambang Batas)
    low_stock_count = InventoryItem.objects.filter(
        quantity__lte=F('reorder_threshold'),
        is_active=True
    ).count()

    # 3. Hitung Pembelian (PO) Pending
    pending_purchases_count = PurchaseOrder.objects.filter(
        status=PurchaseOrder.StatusChoices.PENDING
    ).count()

    # 4. Hitung Pengeluaran Belum Dibayar (Gaji, Tagihan, dll)
    unpaid_expenses_count = Expense.objects.filter(
        status=Expense.StatusChoices.PENDING
    ).count()

    # Total Notifikasi
    total_notifications = (
        pending_transactions_count + 
        low_stock_count + 
        pending_purchases_count + 
        unpaid_expenses_count
    )

    return {
        'notif_counts': {
            'total': total_notifications,
            'transactions': pending_transactions_count,
            'low_stock': low_stock_count,
            'purchases': pending_purchases_count,
            'expenses': unpaid_expenses_count,
        }
    }