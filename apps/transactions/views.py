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


    # apps/transactions/views.py

# Import Library Printer
from escpos.printer import Usb
from escpos.exceptions import USBNotFoundError, Error as EscposError

import usb.core
import usb.util

@login_required
def transaction_print_direct(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    # ID Printer QPOS (Sesuai lsusb kamu)
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x070b

    try:
        # 1. Cari Printer
        printer = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if printer is None:
            messages.error(request, "Printer USB Tidak Ditemukan! Cek kabel.")
            return redirect('transactions:transaction_detail', pk=pk)

        # 2. Detach Kernel Driver (Supaya Linux tidak memonopoli printer)
        try:
            if printer.is_kernel_driver_active(0):
                printer.detach_kernel_driver(0)
        except usb.core.USBError:
            pass # Abaikan jika gagal detach

        # 3. Set Config
        printer.set_configuration()
        cfg = printer.get_active_configuration()
        intf = cfg[(0, 0)]

        # 4. Cari Endpoint OUT (Pintu Keluar Data)
        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )

        if ep_out is None:
            messages.error(request, "Endpoint Printer Bermasalah.")
            return redirect('transactions:transaction_detail', pk=pk)

        # --- FUNGSI KIRIM TEXT ---
        def print_text(text):
            # Encode ke format yg dimengerti printer china (GB18030 atau CP437)
            ep_out.write(text.encode('gb18030', errors='ignore'))

        # --- MULAI CETAK (ESC/POS COMMANDS) ---
        
        # Command Dasar
        CMD_INIT = b'\x1b\x40'
        CMD_CENTER = b'\x1b\x61\x01'
        CMD_LEFT = b'\x1b\x61\x00'
        CMD_RIGHT = b'\x1b\x61\x02'
        CMD_CUT = b'\x1d\x56\x00'
        
        # Kirim Init
        ep_out.write(CMD_INIT)
        
        # Header
        ep_out.write(CMD_CENTER)
        print_text("JATIWANGI MOTOR\n")
        print_text("Jl. Raya President Univ\n")
        print_text("--------------------------------\n")
        
        # Info
        ep_out.write(CMD_LEFT)
        print_text(f"No Inv : {txn.invoice_number}\n")
        print_text(f"Tgl    : {txn.created_at.strftime('%d/%m/%y %H:%M')}\n")
        print_text(f"Plg    : {txn.customer.name if txn.customer else 'Umum'}\n")
        print_text(f"Mekanik: {txn.mechanic.name if txn.mechanic else '-'}\n")
        print_text("--------------------------------\n")
        
        # Items
        for item in txn.items.all():
            print_text(f"{item.item.name[:30]}\n") # Nama barang
            
            # Hitung string harga
            qty = str(item.quantity)
            price = f"{item.unit_price:,.0f}".replace(",", ".")
            subtotal = f"{item.subtotal:,.0f}".replace(",", ".")
            
            print_text(f"{qty} x {price} = {subtotal}\n")

        # Services
        for svc in txn.services.all():
            print_text(f"{svc.service.name[:30]}\n")
            
            qty = str(svc.quantity)
            price = f"{svc.unit_price:,.0f}".replace(",", ".")
            subtotal = f"{svc.subtotal:,.0f}".replace(",", ".")
            
            print_text(f"{qty} x {price} = {subtotal}\n")
            
        print_text("--------------------------------\n")
        
        # Total
        ep_out.write(CMD_RIGHT)
        if txn.discount_amount > 0:
            disc = f"{txn.discount_amount:,.0f}".replace(",", ".")
            print_text(f"Diskon: -{disc}\n")
            
        grand_total = f"{txn.total_amount:,.0f}".replace(",", ".")
        print_text(f"TOTAL: Rp {grand_total}\n")
        
        # Footer
        ep_out.write(CMD_CENTER)
        print_text("\n")
        print_text("Terima Kasih\n")
        print_text("Barang yg dibeli tdk dpt ditukar\n")
        print_text("\n\n\n") # Feed kertas sedikit
        
        # Potong
        ep_out.write(CMD_CUT)

        messages.success(request, "Struk berhasil dicetak (USB Direct)!")

    except Exception as e:
        # Tangkap error biar web gak crash
        messages.error(request, f"Gagal Print USB: {str(e)}")

    return redirect('transactions:transaction_detail', pk=pk)