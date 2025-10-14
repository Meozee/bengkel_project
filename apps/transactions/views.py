# ===== apps/transactions/views.py =====
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.contrib import messages
from .models import Transaction, TransactionItem, TransactionService
from .forms import TransactionForm, TransactionItemFormSet, TransactionServiceFormSet
from apps.inventory.models import InventoryItem


def transaction_list_view(request):
    transactions = Transaction.objects.all().order_by('-transaction_date')
    return render(request, 'transactions/transaction_list.html', {'transactions': transactions})


def item_autocomplete(request):
    query = request.GET.get('q', '').strip()
    if not query:
        return JsonResponse([], safe=False)

    items = InventoryItem.objects.filter(name__icontains=query).order_by('name')[:15]
    data = [
        {
            "id": item.id,
            "name": item.name,
            "price": float(item.sell_price or 0)
        }
        for item in items
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
                    transaction_obj = form.save()
                    
                    # Save items
                    item_formset.instance = transaction_obj
                    item_formset.save()
                    
                    # Save services
                    service_formset.instance = transaction_obj
                    service_formset.save()

                messages.success(request, f"Transaksi {transaction_obj.invoice_number} berhasil disimpan!")
                return redirect('transactions:transaction_list')
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")
        else:
            messages.error(request, "Terdapat kesalahan pada form. Silakan periksa kembali.")
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
    }
    return render(request, 'transactions/transaction_form.html', context)