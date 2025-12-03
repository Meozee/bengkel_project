# apps/transactions/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError

# Import Library USB Raw (Sesuai tes berhasil)
import usb.core
import usb.util

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
    
    # 1. Filter Keyword
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

    # 3. Filter Tanggal
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            txns = txns.filter(created_at__range=(start_date, end_date))
        except ValueError:
            pass 

    context = {
        'transactions': txns,
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
# CRUD VIEWS (CREATE & EDIT DENGAN PERBAIKAN TOTAL)
# ====================================================================

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        # PENTING: Gunakan prefix agar data formset terbaca dengan benar oleh Django
        item_formset = TransactionItemFormSet(request.POST, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, prefix='services')
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            try:
                with transaction.atomic():
                    # 1. Simpan Header Transaksi
                    txn = form.save()
                    
                    # 2. Simpan Items (Barang)
                    items = item_formset.save(commit=False)
                    for item in items:
                        item.transaction = txn
                        item.save()
                    
                    # 3. Simpan Services (Jasa)
                    services = service_formset.save(commit=False)
                    for svc in services:
                        svc.transaction = txn
                        svc.save()
                    
                    # 4. HITUNG ULANG TOTAL (Wajib untuk akurasi)
                    # Kita refresh dari DB atau hitung manual dari object yang baru disimpan
                    total_items = sum(i.subtotal for i in txn.items.all())
                    total_services = sum(s.subtotal for s in txn.services.all())
                    
                    txn.total_amount = total_items + total_services + txn.other_charges - txn.discount_amount
                    txn.save() # Simpan ulang total amount yang benar
                    
                    log_activity(request, 'CREATE', 'Transaction', txn.pk, f"Membuat transaksi baru {txn.invoice_number}")
                    
                    messages.success(request, f"Transaksi {txn.invoice_number} berhasil dibuat.")
                    return redirect('transactions:transaction_list')
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan sistem: {e}")
        else:
            messages.error(request, "Gagal menyimpan. Mohon periksa kelengkapan input.")
    else:
        # GET Request: Form kosong
        form = TransactionForm()
        item_formset = TransactionItemFormSet(prefix='items')
        service_formset = TransactionServiceFormSet(prefix='services')

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
        # PENTING: Pass instance=txn dan prefix
        item_formset = TransactionItemFormSet(request.POST, instance=txn, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, instance=txn, prefix='services')
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            try:
                with transaction.atomic():
                    txn = form.save()
                    
                    # Save formsets (Ini otomatis handle update, create, DAN delete jika can_delete=True)
                    item_formset.save()
                    service_formset.save()
                    
                    # Hitung Ulang Total
                    total_items = sum(i.subtotal for i in txn.items.all())
                    total_services = sum(s.subtotal for s in txn.services.all())
                    
                    txn.total_amount = total_items + total_services + txn.other_charges - txn.discount_amount
                    txn.save()
                    
                    log_activity(request, 'UPDATE', 'Transaction', txn.pk, f"Mengedit transaksi {txn.invoice_number}")
                    
                    messages.success(request, "Transaksi berhasil diperbarui.")
                    return redirect('transactions:transaction_list')
            except Exception as e:
                messages.error(request, f"Error: {e}")
        else:
             messages.error(request, "Gagal update. Cek kembali form.")
    else:
        # GET Request: Isi dengan data lama
        form = TransactionForm(instance=txn)
        item_formset = TransactionItemFormSet(instance=txn, prefix='items')
        service_formset = TransactionServiceFormSet(instance=txn, prefix='services')

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
# ACTIONS
# ====================================================================

@login_required
def update_status(request, pk, new_status):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if new_status not in Transaction.StatusChoices.values:
        messages.error(request, "Status tidak valid.")
        return redirect('transactions:transaction_list')

    try:
        # ATOMIC: Ini kuncinya! 
        # Jika ada error di signals (stok kurang), perubahan txn.status juga dibatalkan.
        with transaction.atomic():
            txn.status = new_status
            txn.save()  # Signal stok berjalan di sini
            
            log_activity(request, 'UPDATE_STATUS', 'Transaction', txn.pk, f"Mengubah status ke {new_status}")
            messages.success(request, f"Status berubah menjadi {txn.get_status_display()}")
            
    except ValidationError as e:
        # Tangkap pesan error dari signals.py (Stok kurang)
        # Status di database otomatis ROLLBACK (tetap Pending)
        messages.error(request, f"Gagal update status: {e.messages[0] if hasattr(e, 'messages') else str(e)}")
        
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan sistem: {str(e)}")
        
    return redirect('transactions:transaction_list')


# ====================================================================
# PRINTING LOGIC (RAW USB & HTML)
# ====================================================================

@login_required
def transaction_print_direct(request, pk):
    """
    Fungsi Direct Print ke USB Thermal Printer (QPOS 58mm).
    Menggunakan Raw USB (pyusb) - ID: 0483:070b
    """
    txn = get_object_or_404(Transaction, pk=pk)
    
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x070b

    try:
        dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if dev is None:
            messages.error(request, "Printer USB Tidak Ditemukan! Cek kabel.")
            return redirect('transactions:transaction_detail', pk=pk)

        try:
            if dev.is_kernel_driver_active(0):
                dev.detach_kernel_driver(0)
        except:
            pass

        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]
        
        ep_out = usb.util.find_descriptor(
            intf,
            custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT
        )

        if ep_out is None:
            messages.error(request, "Endpoint Printer Bermasalah.")
            return redirect('transactions:transaction_detail', pk=pk)

        # Helper
        def send(text):
            ep_out.write(text.encode('gb18030', errors='ignore'))

        # --- ESC/POS COMMANDS ---
        CMD_INIT = b'\x1b\x40'
        CMD_CENTER = b'\x1b\x61\x01'
        CMD_LEFT = b'\x1b\x61\x00'
        CMD_RIGHT = b'\x1b\x61\x02'
        CMD_BOLD_ON = b'\x1b\x45\x01'
        CMD_BOLD_OFF = b'\x1b\x45\x00'
        CMD_CUT = b'\x1d\x56\x00'
        CMD_FEED = b'\n'

        # --- PRINTING PROCESS ---
        ep_out.write(CMD_INIT)
        
        # Header
        ep_out.write(CMD_CENTER)
        ep_out.write(CMD_BOLD_ON)
        send("JATIWANGI MOTOR\n")
        ep_out.write(CMD_BOLD_OFF)
        send("Jl. Raya President Univ\n")
        send("--------------------------------\n")
        
        # Info
        ep_out.write(CMD_LEFT)
        send(f"No Inv : {txn.invoice_number}\n")
        send(f"Tgl    : {txn.created_at.strftime('%d/%m/%y %H:%M')}\n")
        send(f"Plg    : {txn.customer.name if txn.customer else 'Umum'}\n")
        send(f"Mekanik: {txn.mechanic.name if txn.mechanic else '-'}\n")
        send("--------------------------------\n")
        
        # Items
        for item in txn.items.all():
            send(f"{item.item.name[:30]}\n")
            qty = str(item.quantity)
            price = f"{item.unit_price:,.0f}".replace(",", ".")
            subtotal = f"{item.subtotal:,.0f}".replace(",", ".")
            send(f"{qty} x {price} = {subtotal}\n")

        # Services
        for svc in txn.services.all():
            send(f"{svc.service.name[:30]}\n")
            qty = str(svc.quantity)
            price = f"{svc.unit_price:,.0f}".replace(",", ".")
            subtotal = f"{svc.subtotal:,.0f}".replace(",", ".")
            send(f"{qty} x {price} = {subtotal}\n")
            
        send("--------------------------------\n")
        
        # Total
        ep_out.write(CMD_RIGHT)
        if txn.discount_amount > 0:
            disc = f"{txn.discount_amount:,.0f}".replace(",", ".")
            send(f"Diskon: -{disc}\n")
            
        grand_total = f"{txn.total_amount:,.0f}".replace(",", ".")
        ep_out.write(CMD_BOLD_ON)
        send(f"TOTAL: Rp {grand_total}\n")
        ep_out.write(CMD_BOLD_OFF)
        
        # Footer
        ep_out.write(CMD_CENTER)
        send("\n")
        send("Terima Kasih\n")
        send("Barang yg dibeli tdk dpt ditukar\n")
        
        ep_out.write(CMD_FEED * 4) 
        ep_out.write(CMD_CUT)

        messages.success(request, "Struk berhasil dicetak (USB Direct)!")

    except Exception as e:
        messages.error(request, f"Gagal Print USB: {str(e)}")

    finally:
        # --- INI SOLUSI RESOURCE BUSY ---
        # Wajib lepas resource agar bisa dipake lagi
        if dev is not None:
            usb.util.dispose_resources(dev)

    return redirect('transactions:transaction_detail', pk=pk)


@login_required
def transaction_print(request, pk):
    """HTML Print View (Backup/Preview)."""
    txn = get_object_or_404(Transaction, pk=pk)
    context = {
        'transaction': txn,
        'items': txn.items.all(),
        'services': txn.services.all(),
        'shop_name': "BENGKEL JATIWANGI MOTOR",
        'shop_address': "Jl. Raya President Univ",
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