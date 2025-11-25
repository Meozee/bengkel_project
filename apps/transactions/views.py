# apps/transactions/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

# Security & Logs
from apps.accounts.decorators import owner_required
from apps.accounts.utils import log_activity

# Models & Forms
from .models import Transaction, TransactionItem, TransactionService
from .forms import TransactionForm, TransactionItemFormSet, TransactionServiceFormSet
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service

# ====================================================================
# LIST & DETAIL VIEWS
# ====================================================================

@login_required
def transaction_list(request):
    """Menampilkan daftar transaksi dengan filter lengkap."""
    txns = Transaction.objects.select_related('customer', 'vehicle', 'mechanic').all()
    
    # 1. Filter Keyword (Nama Pelanggan/Mekanik/Plat)
    customer_name = request.GET.get('customer_name')
    if customer_name:
        txns = txns.filter(customer__name__icontains=customer_name)
        
    mechanic_name = request.GET.get('mechanic_name')
    if mechanic_name:
        txns = txns.filter(mechanic__name__icontains=mechanic_name)
        
    license_plate = request.GET.get('license_plate')
    if license_plate:
        txns = txns.filter(vehicle__license_plate__icontains=license_plate)

    # 2. Filter Status
    status = request.GET.get('status')
    if status:
        txns = txns.filter(status=status)

    # 3. Filter Tanggal (Range)
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            # Konversi string ke datetime
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            # Set end_date ke akhir hari tersebut (23:59:59)
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            
            txns = txns.filter(created_at__range=(start_date, end_date))
        except ValueError:
            pass # Abaikan jika format tanggal salah

    context = {
        'transactions': txns,
        # Kirim balik value ke template agar input tidak reset
        'filter_customer': customer_name or '',
        'filter_mechanic': mechanic_name or '',
        'filter_plate': license_plate or '',
        'filter_status': status or '',
        'filter_start': start_date_str or '',
        'filter_end': end_date_str or '',
    }
    return render(request, 'transactions/transaction_list.html', context)


@login_required
def transaction_detail(request, pk):
    """View untuk melihat detail lengkap transaksi (Invoice)."""
    txn = get_object_or_404(Transaction, pk=pk)
    context = {
        'transaction': txn,
        'title': f"Detail {txn.invoice_number}"
    }
    return render(request, 'transactions/transaction_detail.html', context)


# ====================================================================
# CRUD VIEWS (Create, Edit, Delete)
# ====================================================================

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        item_formset = TransactionItemFormSet(request.POST)
        service_formset = TransactionServiceFormSet(request.POST)
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            try:
                with transaction.atomic():
                    txn = form.save()
                    
                    items = item_formset.save(commit=False)
                    for item in items:
                        item.transaction = txn
                        item.save()
                    
                    services = service_formset.save(commit=False)
                    for svc in services:
                        svc.transaction = txn
                        svc.save()
                    
                    log_activity(request, 'CREATE', 'Transaction', txn.pk, f"Membuat transaksi baru {txn.invoice_number}")
                    
                    messages.success(request, f"Transaksi {txn.invoice_number} berhasil dibuat.")
                    return redirect('transactions:transaction_list')
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan sistem: {e}")
        else:
            messages.error(request, "Mohon periksa kembali inputan form.")
    else:
        form = TransactionForm()
        item_formset = TransactionItemFormSet()
        service_formset = TransactionServiceFormSet()

    context = {
        'form': form,
        'item_formset': item_formset,
        'service_formset': service_formset,
        'title': 'Buat Transaksi Baru'
    }
    return render(request, 'transactions/transaction_form.html', context)


@login_required
def transaction_edit(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if txn.status == Transaction.StatusChoices.CANCELLED:
        messages.error(request, "Transaksi yang sudah dibatalkan tidak bisa diedit.")
        return redirect('transactions:transaction_list')

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=txn)
        item_formset = TransactionItemFormSet(request.POST, instance=txn)
        service_formset = TransactionServiceFormSet(request.POST, instance=txn)
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    item_formset.save()
                    service_formset.save()
                    
                    log_activity(request, 'UPDATE', 'Transaction', txn.pk, f"Mengedit transaksi {txn.invoice_number}")
                    
                    messages.success(request, "Transaksi berhasil diperbarui.")
                    return redirect('transactions:transaction_list')
            except Exception as e:
                messages.error(request, f"Error: {e}")
    else:
        form = TransactionForm(instance=txn)
        item_formset = TransactionItemFormSet(instance=txn)
        service_formset = TransactionServiceFormSet(instance=txn)

    context = {
        'form': form,
        'item_formset': item_formset,
        'service_formset': service_formset,
        'transaction': txn,
        'title': f'Edit Transaksi {txn.invoice_number}'
    }
    return render(request, 'transactions/transaction_form.html', context)


@owner_required
def transaction_delete(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        invoice = txn.invoice_number
        txn.delete()
        log_activity(request, 'DELETE', 'Transaction', invoice, "Menghapus transaksi permanent")
        messages.success(request, "Transaksi berhasil dihapus.")
        return redirect('transactions:transaction_list')
        
    return redirect('transactions:transaction_list')


# ====================================================================
# ACTIONS (Status & Print)
# ====================================================================

@login_required
def update_status(request, pk, new_status):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if new_status not in Transaction.StatusChoices.values:
        messages.error(request, "Status tidak valid.")
        return redirect('transactions:transaction_list')

    try:
        txn.status = new_status
        txn.save() 
        
        log_activity(request, 'UPDATE_STATUS', 'Transaction', txn.pk, f"Mengubah status ke {new_status}")
        messages.success(request, f"Status berubah menjadi {txn.get_status_display()}")
            
    except Exception as e:
        messages.error(request, f"Gagal update status: {e}")
        
    return redirect('transactions:transaction_list')


@login_required
def transaction_print(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if 'print_invoice_id' in request.session:
        del request.session['print_invoice_id']
        
    context = {
        'transaction': txn,
        'items': txn.items.all(),
        'services': txn.services.all(),
        'shop_name': "BENGKEL JATIWANGI MOTOR",
        'shop_address': "Jl. Raya Presiden University, Cikarang",
        'shop_phone': "0812-3456-7890",
    }
    return render(request, 'transactions/transaction_print.html', context)


# ====================================================================
# API HELPER (AJAX Calls)
# ====================================================================

@login_required
def api_get_item_price(request, item_id):
    item = get_object_or_404(InventoryItem, pk=item_id)
    return JsonResponse({'price': item.sell_price})

@login_required
def api_get_service_price(request, service_id):
    svc = get_object_or_404(Service, pk=service_id)
    return JsonResponse({'price': svc.price})