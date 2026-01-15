# apps/accounts/views.py

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.timezone import make_aware 
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm

# Import model & utility custom
from .models import ActivityLog, CustomUser
from .decorators import owner_required
from .utils import log_activity 

@login_required
@owner_required
def activity_log_view(request):
    # 1. Base Query
    logs = ActivityLog.objects.select_related('user').all().order_by('-timestamp')

    # --- FILTER PENCARIAN ---
    search_query = request.GET.get('q', '')
    if search_query:
        logs = logs.filter(
            Q(user__username__icontains=search_query) | 
            Q(action_type__icontains=search_query) |
            Q(details__icontains=search_query) |
            Q(target_model__icontains=search_query)
        )

    # --- FILTER USER ---
    user_id = request.GET.get('user')
    if user_id:
        logs = logs.filter(user_id=user_id)

    # --- FILTER TANGGAL ---
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_naive = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_naive = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            
            start_date = make_aware(start_naive)
            end_date = make_aware(end_naive)
            
            logs = logs.filter(timestamp__range=(start_date, end_date))
        except ValueError:
            pass

    # --- PEMBAGIAN DATA UNTUK TAB ---
    LIMIT = 100 
    
    logs_auth = logs.filter(action_type__in=['LOGIN', 'LOGOUT', 'UPDATE_PASSWORD'])[:LIMIT]
    logs_transaction = logs.filter(target_model='Transaction')[:LIMIT]
    logs_inventory = logs.filter(target_model__in=['InventoryItem', 'Category'])[:LIMIT]
    logs_finance = logs.filter(target_model__in=['Expense', 'ExpenseCategory', 'PurchaseOrder', 'RecurringExpense'])[:LIMIT]
    logs_master = logs.filter(target_model__in=['Customer', 'Mechanic', 'Vehicle', 'Service', 'Vendor'])[:LIMIT]
    logs_reports = logs.filter(Q(target_model__startswith='Report') | Q(target_model__in=['FinancialReport', 'InventoryReport', 'CustomerReport', 'MechanicReport']))[:LIMIT]

    # --- JEBAKAN DEBUG TERMINAL (Cek Terminal VSCode Bawah) ---
    print("\n" + "="*30)
    print("=== DEBUG LOG AKTIVITAS ===")
    print(f"User Request: {request.user}")
    print(f"Total Log (Filtered): {logs.count()}")
    print(f" - Auth: {logs_auth.count()}")
    print(f" - Transaksi: {logs_transaction.count()}")
    print(f" - Inventory: {logs_inventory.count()}")
    print(f" - Laporan: {logs_reports.count()}")
    print("="*30 + "\n")
    # ----------------------------------------------------------

    users = CustomUser.objects.all()

    context = {
        'page_title': 'Log Aktivitas Sistem',
        'logs_auth': logs_auth,
        'logs_transaction': logs_transaction,
        'logs_inventory': logs_inventory,
        'logs_finance': logs_finance,
        'logs_master': logs_master,
        'logs_reports': logs_reports,
        
        'users': users,
        'current_search': search_query,
        'current_user': int(user_id) if user_id else '',
        'start_date': start_date_str or '',
        'end_date': end_date_str or '',
    }

    return render(request, 'accounts/activity_log.html', context)


@login_required
def change_password_view(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  
            
            log_activity(
                request, 'UPDATE_PASSWORD', 'User', user.id, 
                f'User {user.username} berhasil mengubah password akun.'
            )

            messages.success(request, 'Password berhasil diperbarui!')
            return redirect('dashboard:index') 
        else:
            messages.error(request, 'Terjadi kesalahan. Silakan periksa kembali inputan Anda.')
    else:
        form = PasswordChangeForm(request.user)
        
    return render(request, 'accounts/change_password.html', {'form': form})