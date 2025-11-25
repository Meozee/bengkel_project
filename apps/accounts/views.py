# apps/accounts/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone

from .models import ActivityLog, CustomUser
from .decorators import owner_required

@login_required
@owner_required
def activity_log_view(request):
    # 1. Base Query
    logs = ActivityLog.objects.select_related('user').all().order_by('-timestamp')

    # --- FILTER LOGIC ---
    search_query = request.GET.get('q', '')
    if search_query:
        logs = logs.filter(
            Q(user__username__icontains=search_query) | 
            Q(action_type__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(target_model__icontains=search_query)
        )

    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            logs = logs.filter(timestamp__range=(start_date, end_date))
        except ValueError:
            pass

    # --- PEMBAGIAN TAB ---
    LIMIT = 100 
    
    # Tab 1: Login
    logs_auth = logs.filter(action_type__in=['LOGIN', 'LOGOUT'])[:LIMIT]
    
    # Tab 2: Transaksi
    logs_transaction = logs.filter(target_model='Transaction')[:LIMIT]
    
    # Tab 3: Inventory (Hapus Report dari sini)
    logs_inventory = logs.filter(target_model__in=['InventoryItem', 'Category'])[:LIMIT]
    
    # Tab 4: Keuangan (Hapus Report dari sini)
    logs_finance = logs.filter(
        target_model__in=['Expense', 'ExpenseCategory', 'PurchaseOrder']
    )[:LIMIT]
    
    # Tab 5: Data Master (Hapus Report dari sini)
    logs_master = logs.filter(
        target_model__in=['Customer', 'Mechanic', 'Vehicle', 'Service', 'Vendor']
    )[:LIMIT]

    # Tab 6: LAPORAN (BARU)
    # Menangkap target yang diawali "Report" atau nama report lama
    logs_reports = logs.filter(
        Q(target_model__startswith='Report') | 
        Q(target_model__in=['FinancialReport', 'InventoryReport', 'CustomerReport', 'MechanicReport'])
    )[:LIMIT]

    users = CustomUser.objects.all()

    context = {
        'page_title': 'Log Aktivitas Sistem',
        'logs_auth': logs_auth,
        'logs_transaction': logs_transaction,
        'logs_inventory': logs_inventory,
        'logs_finance': logs_finance,
        'logs_master': logs_master,
        'logs_reports': logs_reports, # <-- Data Tab Baru
        
        'users': users,
        'current_search': search_query,
        'current_user': int(user_id) if user_id else '',
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
    }

    return render(request, 'accounts/activity_log.html', context)