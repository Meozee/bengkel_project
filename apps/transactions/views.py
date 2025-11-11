from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from decimal import Decimal
from datetime import datetime
from .models import Transaction, TransactionItem, TransactionService
from .forms import TransactionForm, TransactionItemFormSet, TransactionServiceFormSet
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service, Customer, Vehicle, Mechanic


def transaction_list(request):
    """List transaksi dengan filter lengkap"""
    transactions = Transaction.objects.select_related(
        'customer', 'vehicle', 'mechanic'
    ).all()
    
    # Filter berdasarkan nama pelanggan
    customer_name = request.GET.get('customer_name', '').strip()
    if customer_name:
        transactions = transactions.filter(
            customer__name__icontains=customer_name
        )
    
    # Filter berdasarkan nama mekanik
    mechanic_name = request.GET.get('mechanic_name', '').strip()
    if mechanic_name:
        transactions = transactions.filter(
            mechanic__name__icontains=mechanic_name
        )
    
    # Filter berdasarkan plat nomor
    license_plate = request.GET.get('license_plate', '').strip()
    if license_plate:
        transactions = transactions.filter(
            vehicle__license_plate__icontains=license_plate
        )
    
    # Filter berdasarkan jenis motor
    vehicle_type = request.GET.get('vehicle_type', '').strip()
    if vehicle_type:
        transactions = transactions.filter(
            vehicle__vehicle_type__icontains=vehicle_type
        )
    
    # Filter berdasarkan status
    status = request.GET.get('status', '').strip()
    if status:
        transactions = transactions.filter(status=status)
    
    # Filter berdasarkan tanggal
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
            transactions = transactions.filter(transaction_date__gte=date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')
            transactions = transactions.filter(transaction_date__lte=date_to_obj)
        except ValueError:
            pass
    
    # Filter bulan ini
    if request.GET.get('this_month'):
        from django.utils import timezone
        now = timezone.now()
        transactions = transactions.filter(
            transaction_date__year=now.year,
            transaction_date__month=now.month
        )
    
    context = {
        'transactions': transactions,
        'status_choices': Transaction.StatusChoices.choices,
        'filters': request.GET
    }
    
    return render(request, 'transactions/transaction_list.html', context)


def transaction_create(request):
    """Form untuk membuat transaksi baru"""
    if request.method == 'POST':
        form = TransactionForm(request.POST)
        item_formset = TransactionItemFormSet(request.POST, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, prefix='services')
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            # Simpan transaksi
            transaction = form.save(commit=False)
            
            # Generate invoice number jika belum ada
            if not transaction.invoice_number:
                from django.utils import timezone
                now = timezone.now()
                last_invoice = Transaction.objects.filter(
                    transaction_date__year=now.year,
                    transaction_date__month=now.month
                ).order_by('-id').first()
                
                if last_invoice and last_invoice.invoice_number:
                    try:
                        last_num = int(last_invoice.invoice_number.split('-')[-1])
                        new_num = last_num + 1
                    except (ValueError, IndexError):
                        new_num = 1
                else:
                    new_num = 1
                
                transaction.invoice_number = f"INV-{now.strftime('%Y%m')}-{new_num:04d}"
            
            transaction.save()
            
            # Simpan items
            items = item_formset.save(commit=False)
            for item in items:
                if item.item and item.quantity > 0:
                    item.transaction = transaction
                    item.save()
            
            # Simpan services
            services = service_formset.save(commit=False)
            for service in services:
                if service.service and service.quantity > 0:
                    service.transaction = transaction
                    service.save()
            
            # Hitung total
            total = Decimal('0.00')
            for item in transaction.items.all():
                total += item.subtotal
            for service in transaction.services.all():
                total += service.subtotal
            
            total += transaction.other_charges
            total -= transaction.discount_amount
            
            transaction.total_amount = total
            transaction.save()
            
            messages.success(request, f'Transaksi {transaction.invoice_number} berhasil dibuat!')
            return redirect('transactions:transaction_list')
    else:
        form = TransactionForm()
        item_formset = TransactionItemFormSet(prefix='items', queryset=TransactionItem.objects.none())
        service_formset = TransactionServiceFormSet(prefix='services', queryset=TransactionService.objects.none())
    
    context = {
        'form': form,
        'item_formset': item_formset,
        'service_formset': service_formset,
    }
    
    return render(request, 'transactions/transaction_form.html', context)


def transaction_edit(request, pk):
    """Form untuk edit transaksi"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        form = TransactionForm(request.POST, instance=transaction)
        item_formset = TransactionItemFormSet(request.POST, instance=transaction, prefix='items')
        service_formset = TransactionServiceFormSet(request.POST, instance=transaction, prefix='services')
        
        if form.is_valid() and item_formset.is_valid() and service_formset.is_valid():
            transaction = form.save()
            item_formset.save()
            service_formset.save()
            
            # Hitung ulang total
            total = Decimal('0.00')
            for item in transaction.items.all():
                total += item.subtotal
            for service in transaction.services.all():
                total += service.subtotal
            
            total += transaction.other_charges
            total -= transaction.discount_amount
            
            transaction.total_amount = total
            transaction.save()
            
            messages.success(request, f'Transaksi {transaction.invoice_number} berhasil diupdate!')
            return redirect('transactions:transaction_list')
    else:
        form = TransactionForm(instance=transaction)
        item_formset = TransactionItemFormSet(instance=transaction, prefix='items')
        service_formset = TransactionServiceFormSet(instance=transaction, prefix='services')
    
    context = {
        'form': form,
        'item_formset': item_formset,
        'service_formset': service_formset,
        'transaction': transaction,
    }
    
    return render(request, 'transactions/transaction_form.html', context)


def transaction_delete(request, pk):
    """Hapus transaksi"""
    transaction = get_object_or_404(Transaction, pk=pk)
    
    if request.method == 'POST':
        invoice_number = transaction.invoice_number
        transaction.delete()
        messages.success(request, f'Transaksi {invoice_number} berhasil dihapus!')
        return redirect('transactions:transaction_list')
    
    return render(request, 'transactions/transaction_confirm_delete.html', {'transaction': transaction})


# API untuk search item
def api_search_items(request):
    """API untuk search inventory items"""
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    items = InventoryItem.objects.filter(
        Q(name__icontains=query) | Q(sku__icontains=query)
    )[:10]
    
    results = [{
        'id': item.id,
        'name': item.name,
        'sku': item.sku or '',
        'sell_price': str(item.sell_price),
        'quantity': item.quantity
    } for item in items]
    
    return JsonResponse({'results': results})


# API untuk get item price
def api_get_item_price(request, item_id):
    """API untuk mendapatkan harga jual item"""
    try:
        item = InventoryItem.objects.get(id=item_id)
        return JsonResponse({
            'sell_price': str(item.sell_price),
            'name': item.name,
            'stock': item.quantity
        })
    except InventoryItem.DoesNotExist:
        return JsonResponse({'error': 'Item not found'}, status=404)


# API untuk get service price
def api_get_service_price(request, service_id):
    """API untuk mendapatkan harga service"""
    try:
        service = Service.objects.get(id=service_id)
        return JsonResponse({
            'price': str(service.price),
            'name': service.name
        })
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)