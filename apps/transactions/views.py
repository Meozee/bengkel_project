from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q, Prefetch
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
import usb.core
import usb.util

from apps.accounts.decorators import owner_required
from apps.accounts.utils import log_activity
from .models import Transaction, TransactionItem, TransactionService, TransactionMisc
from .forms import TransactionForm, TransactionItemFormSet, TransactionServiceFormSet, TransactionMiscFormSet
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service
from django.core.paginator import Paginator

# ====================================================================
# LIST & DETAIL VIEWS
# ====================================================================

@login_required
def transaction_list(request):
    """Menampilkan daftar transaksi dengan filter lengkap."""
    txns = Transaction.objects.select_related('customer', 'vehicle', 'mechanic')\
                              .prefetch_related('items__item', 'services__service', 'miscs').all()
    
    # --- FILTER ---
    customer_name = request.GET.get('customer_name')
    if customer_name: txns = txns.filter(customer__name__icontains=customer_name)
    
    mechanic_name = request.GET.get('mechanic_name')
    if mechanic_name: txns = txns.filter(mechanic__name__icontains=mechanic_name)
    
    license_plate = request.GET.get('license_plate')
    if license_plate: txns = txns.filter(vehicle__license_plate__icontains=license_plate)

    status = request.GET.get('status')
    if status: txns = txns.filter(status=status)

    item_name = request.GET.get('item_name')
    if item_name: txns = txns.filter(items__item__name__icontains=item_name).distinct()

    service_name = request.GET.get('service_name')
    if service_name: txns = txns.filter(services__service__name__icontains=service_name).distinct()

    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
            txns = txns.filter(created_at__range=(start_date, end_date))
        except ValueError:
            pass

    txns = txns.order_by('-created_at')
    
    paginator = Paginator(txns, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'transactions': page_obj,
        'filter_customer': customer_name or '',
        'filter_mechanic': mechanic_name or '',
        'filter_plate': license_plate or '',
        'filter_status': status or '',
        'filter_start': start_date_str or '',
        'filter_end': end_date_str or '',
        'filter_item': item_name or '',
        'filter_service': service_name or '',
    }
    return render(request, 'transactions/transaction_list.html', context)


@login_required
def transaction_detail(request, pk):
    txn = get_object_or_404(
        Transaction.objects.select_related('customer', 'vehicle', 'mechanic')
        .prefetch_related('items__item', 'items__install_service', 'services__service', 'miscs'),
        pk=pk
    )
    context = {'transaction': txn, 'title': f"Detail {txn.invoice_number}"}
    return render(request, 'transactions/transaction_detail.html', context)


# ====================================================================
# CRUD VIEWS (CREATE, EDIT, DELETE)
# ====================================================================

@login_required
def transaction_create(request):
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        item_formset = TransactionItemFormSet(request.POST, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, prefix='services')
        misc_formset = TransactionMiscFormSet(request.POST, prefix='miscs') 

        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid() and misc_formset.is_valid():
            try:
                with transaction.atomic():
                    txn = form.save()
                    
                    items = item_formset.save(commit=False)
                    for item_obj in items:
                        item_obj.transaction = txn
                        item_obj.save()
                    for deleted_item in item_formset.deleted_objects: deleted_item.delete()
                    
                    services = service_formset.save(commit=False)
                    for svc in services:
                        svc.transaction = txn
                        svc.save()
                    for deleted_svc in service_formset.deleted_objects: deleted_svc.delete()

                    miscs = misc_formset.save(commit=False)
                    for misc in miscs:
                        misc.transaction = txn
                        misc.save()
                    for deleted_misc in misc_formset.deleted_objects: deleted_misc.delete()
                    
                    # Update Total
                    total_items = sum(i.subtotal for i in txn.items.all())
                    total_services = sum(s.subtotal for s in txn.services.all())
                    total_miscs = sum(m.subtotal for m in txn.miscs.all())
                    txn.total_amount = total_items + total_services + total_miscs + txn.other_charges - txn.discount_amount
                    txn.save()
                    
                    log_activity(request, 'CREATE', 'Transaction', txn.pk, f"Membuat transaksi {txn.invoice_number}")
                    messages.success(request, f"✅ Transaksi {txn.invoice_number} berhasil dibuat!")
                    return redirect('transactions:transaction_detail', pk=txn.pk)
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")
        else:
            messages.error(request, "❌ Gagal menyimpan. Periksa input form.")
    else:
        form = TransactionForm()
        item_formset = TransactionItemFormSet(prefix='items')
        service_formset = TransactionServiceFormSet(prefix='services')
        misc_formset = TransactionMiscFormSet(prefix='miscs') 

    context = {
        'form': form, 'item_formset': item_formset, 'service_formset': service_formset,
        'misc_formset': misc_formset, 'all_items': InventoryItem.objects.all(), 
        'title': 'Buat Transaksi Baru'
    }
    return render(request, 'transactions/transaction_form.html', context)


@login_required
def transaction_edit(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if not txn.can_be_edited():
        messages.error(request, f"❌ Transaksi {txn.invoice_number} tidak bisa diedit.")
        return redirect('transactions:transaction_detail', pk=pk)

    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=txn)
        item_formset = TransactionItemFormSet(request.POST, instance=txn, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, instance=txn, prefix='services')
        misc_formset = TransactionMiscFormSet(request.POST, instance=txn, prefix='miscs') 
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid() and misc_formset.is_valid():
            try:
                with transaction.atomic():
                    txn = form.save()
                    item_formset.save()
                    service_formset.save()
                    misc_formset.save()
                    
                    total_items = sum(i.subtotal for i in txn.items.all())
                    total_services = sum(s.subtotal for s in txn.services.all())
                    total_miscs = sum(m.subtotal for m in txn.miscs.all())
                    txn.total_amount = total_items + total_services + total_miscs + txn.other_charges - txn.discount_amount
                    txn.save()
                    
                    log_activity(request, 'UPDATE', 'Transaction', txn.pk, f"Mengedit transaksi {txn.invoice_number}")
                    messages.success(request, f"✅ Transaksi {txn.invoice_number} berhasil diperbarui!")
                    return redirect('transactions:transaction_detail', pk=txn.pk)
            except Exception as e:
                messages.error(request, f"❌ Error: {str(e)}")
        else:
            messages.error(request, "❌ Gagal update. Cek kembali form.")
    else:
        form = TransactionForm(instance=txn)
        item_formset = TransactionItemFormSet(instance=txn, prefix='items')
        service_formset = TransactionServiceFormSet(instance=txn, prefix='services')
        misc_formset = TransactionMiscFormSet(instance=txn, prefix='miscs') 

    context = {
        'form': form, 'item_formset': item_formset, 'service_formset': service_formset,
        'misc_formset': misc_formset, 'transaction': txn, 
        'title': f'Edit Transaksi {txn.invoice_number}'
    }
    return render(request, 'transactions/transaction_form.html', context)


@owner_required
def transaction_delete(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if not txn.can_be_deleted():
        messages.error(request, f"❌ Transaksi tidak bisa dihapus.")
        return redirect('transactions:transaction_list')
    
    if request.method == 'POST':
        invoice = txn.invoice_number
        txn.delete()
        log_activity(request, 'DELETE', 'Transaction', invoice, "Menghapus transaksi permanent")
        messages.success(request, f"✅ Transaksi {invoice} berhasil dihapus.")
        return redirect('transactions:transaction_list')
    
    return redirect('transactions:transaction_list')


@login_required
def update_status(request, pk, new_status):
    txn = get_object_or_404(Transaction, pk=pk)
    
    if new_status not in Transaction.StatusChoices.values:
        messages.error(request, "❌ Status tidak valid.")
        return redirect('transactions:transaction_list')

    if txn.status == Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.PENDING:
        messages.error(request, "❌ Transaksi COMPLETED tidak bisa kembali ke PENDING.")
        return redirect('transactions:transaction_list')
    
    if txn.status == Transaction.StatusChoices.CANCELLED:
        messages.error(request, "❌ Transaksi CANCELLED tidak bisa diubah.")
        return redirect('transactions:transaction_list')

    try:
        with transaction.atomic():
            txn.status = new_status
            txn.save() # Signals akan handle stok
            log_activity(request, 'UPDATE_STATUS', 'Transaction', txn.pk, f"Status: {new_status}")
            messages.success(request, f"✅ Status berubah menjadi {txn.get_status_display()}")
            
    except ValidationError as e:
        messages.error(request, f"❌ Gagal update: {e.messages[0] if hasattr(e, 'messages') else str(e)}")
    except Exception as e:
        messages.error(request, f"❌ Terjadi kesalahan: {str(e)}")
        
    return redirect('transactions:transaction_list')


# ====================================================================
# PRINTING & API HELPER
# ====================================================================

@login_required
def transaction_print_direct(request, pk):
    """USB Print Direct (Modified to handle Modular Pricing logic if needed)"""
    txn = get_object_or_404(Transaction, pk=pk)
    
    # ... (Kode USB Print sama, sesuaikan string item + service jika perlu) ...
    # Untuk singkatnya, jika USB print belum urgent, bisa redirect ke detail dulu
    # atau copy paste logic USB dari sebelumnya dan sesuaikan loop items:
    
    VENDOR_ID = 0x0483
    PRODUCT_ID = 0x070b

    try:
        dev = usb.core.find(idVendor=VENDOR_ID, idProduct=PRODUCT_ID)
        if dev is None:
            messages.error(request, "❌ Printer USB Tidak Ditemukan! Cek kabel.")
            return redirect('transactions:transaction_detail', pk=pk)

        try:
            if dev.is_kernel_driver_active(0): dev.detach_kernel_driver(0)
        except: pass

        dev.set_configuration()
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]
        ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

        if ep_out is None:
            messages.error(request, "❌ Endpoint Printer Bermasalah.")
            return redirect('transactions:transaction_detail', pk=pk)

        def send(text): ep_out.write(text.encode('gb18030', errors='ignore'))
        
        # ... Commands ESC/POS (Sama seperti sebelumnya) ...
        CMD_INIT = b'\x1b\x40'
        ep_out.write(CMD_INIT)
        send(f"JATIWANGI MOTOR\nNo Inv: {txn.invoice_number}\n")
        send("-" * 32 + "\n")
        
        for item in txn.items.all():
            send(f"{item.item.name[:30]}\n")
            if item.install_service:
                send(f" + {item.install_service.vehicle_type}\n")
            
            # Print logic (qty x price = subtotal)
            send(f"{item.quantity} x {item.unit_price} = {item.subtotal}\n")
            
        send("-" * 32 + "\n")
        send(f"TOTAL: {txn.total_amount}\n\n")
        ep_out.write(b'\x1d\x56\x00') # Cut

        messages.success(request, "✅ Struk berhasil dicetak (USB Direct)!")

    except Exception as e:
        messages.error(request, f"❌ Gagal Print USB: {str(e)}")
    finally:
        if 'dev' in locals() and dev is not None: usb.util.dispose_resources(dev)

    return redirect('transactions:transaction_detail', pk=pk)


@login_required
def transaction_print(request, pk):
    txn = get_object_or_404(Transaction, pk=pk)
    context = {
        'transaction': txn,
        'items': txn.items.all(),
        'services': txn.services.all(),
        'miscs': txn.miscs.all(),
        'shop_name': "BENGKEL JATIWANGI MOTOR",
        'shop_address': "Jl. Jatiwangi, Cikarang Barat, Bekasi",
        'shop_phone': "0813-8125-0555",
    }
    return render(request, 'transactions/transaction_print.html', context)


@login_required
def api_get_item_price(request, item_id):
    """API: Mengembalikan harga barang DAN list harga jasa pasang (Modular)"""
    try:
        item = get_object_or_404(InventoryItem, pk=item_id)
        
        # 🔥 FIX: Ambil daftar harga jasa dari relation
        service_prices = []
        for sp in item.service_prices.all():
            service_prices.append({
                'id': sp.id,
                'label': f"{sp.vehicle_type} - Rp {sp.price:,.0f}".replace(",", "."),
                'price': float(sp.price)
            })

        return JsonResponse({
            'success': True,
            'price': float(item.sell_price),
            'stock': item.quantity, 
            'name': item.name,
            'service_prices': service_prices # Array of objects
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def api_get_service_price(request, service_id):
    try:
        svc = get_object_or_404(Service, pk=service_id)
        return JsonResponse({'success': True, 'price': float(svc.price), 'name': svc.name})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)