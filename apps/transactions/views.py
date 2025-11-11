# ===== apps/transactions/views.py =====

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.contrib import messages
from django.db.models import Q  # <- Impor Q
from .models import Transaction, TransactionItem, TransactionService
from .forms import TransactionForm, TransactionItemFormSet, TransactionServiceFormSet
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service # ✅ IMPOR SERVICE


def transaction_list_view(request):
    """
    ✅ FUNGSI DIPERBARUI:
    Menambahkan fungsionalitas Search dan Filter.
    """
    # Ambil queryset dasar
    transactions = Transaction.objects.select_related(
        'customer', 'mechanic'
    ).all().order_by('-transaction_date')

    # Ambil parameter GET
    query = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    # Terapkan filter pencarian
    if query:
        transactions = transactions.filter(
            Q(invoice_number__icontains=query) |
            Q(customer__name__icontains=query) |
            Q(vehicle__license_plate__icontains=query)
        )

    # Terapkan filter status
    if status:
        transactions = transactions.filter(status=status)

    context = {
        'transactions': transactions,
        'status_choices': Transaction.StatusChoices.choices,
        'current_query': query,
        'current_status': status,
    }
    return render(request, 'transactions/transaction_list.html', context)


def item_autocomplete(request):
    """
    Autocomplete untuk InventoryItem.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    items = InventoryItem.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query)
    ).order_by('name')[:15]

    data = [
        {
            "id": item.id,
            "text": f"{item.name} (Stok: {item.quantity})",
            # Pastikan ini 'sell_price' sesuai model inventory
            "price": float(item.sell_price or 0)
        }
        for item in items
    ]
    return JsonResponse(data, safe=False)


# ✅ TAMBAHKAN FUNGSI BARU INI
def service_autocomplete(request):
    """
    Autocomplete untuk Service.
    """
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    services = Service.objects.filter(name__icontains=query).order_by('name')[:15]

    data = [
        {
            "id": service.id,
            "text": f"{service.name} (Rp {service.price:,.0f})",
            # Pastikan ini 'price' sesuai model master_data
            "price": float(service.price or 0) 
        }
        for service in services
    ]
    return JsonResponse(data, safe=False)


def transaction_create_or_update_view(request, pk=None):
    """View untuk create dan update transaksi"""
    transaction_obj = get_object_or_404(Transaction, pk=pk) if pk else None
    
    if request.method == "POST":
        form = TransactionForm(request.POST, instance=transaction_obj)
        item_formset = TransactionItemFormSet(request.POST, instance=transaction_obj, prefix="items")
        service_formset = TransactionServiceFormSet(request.POST, instance=transaction_obj, prefix="services")

        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            try:
                with db_transaction.atomic():
                    # Cek validasi stok secara manual SEBELUM menyimpan
                    if not transaction_obj or transaction_obj.status != 'PAID':
                        for form_item in item_formset.cleaned_data:
                            if not form_item: continue
                            
                            item = form_item.get('item')
                            quantity = form_item.get('quantity')
                            
                            if item and quantity:
                                if quantity > item.quantity:
                                    messages.error(request, f"Stok tidak cukup untuk {item.name}. Sisa stok: {item.quantity}.")
                                    raise Exception("Validasi stok gagal.")

                    # Jika lolos, simpan semuanya
                    transaction_instance = form.save()
                    
                    item_formset.instance = transaction_instance
                    item_formset.save()
                    
                    service_formset.instance = transaction_instance
                    service_formset.save()

                messages.success(request, f"Transaksi {transaction_instance.invoice_number} berhasil disimpan!")
                return redirect('transactions:transaction_list')
            except Exception as e:
                # Jika validasi stok gagal, error sudah di-set
                if "Validasi stok gagal" not in str(e):
                    messages.error(request, f"Error: {str(e)}")
        else:
            messages.error(request, "Terdapat kesalahan pada form. Silakan periksa kembali.")
            # Ini akan membantu debugging di console
            print("Form errors:", form.errors)
            print("Item formset errors:", item_formset.errors)
            print("Service formset errors:", service_formset.errors)

    else:
        form = TransactionForm(instance=transaction_obj)
        item_formset = TransactionItemFormSet(instance=transaction_obj, prefix="items")
        service_formset = TransactionServiceFormSet(instance=transaction_obj, prefix="services")

    context = {
        'form': form,
        'item_formset': item_formset,
        'service_formset': service_formset,
        'transaction': transaction_obj,
        'title': f'Edit Transaksi {transaction_obj.invoice_number}' if pk else 'Buat Transaksi Baru'
    }
    return render(request, 'transactions/transaction_form.html', context)