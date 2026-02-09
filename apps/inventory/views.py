from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F, Count
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import transaction # Import transaction atomic

# Import Security & Logging Custom
try:
    from apps.accounts.utils import log_activity
except ImportError:
    def log_activity(request, **kwargs):
        pass

from .models import InventoryItem, Category, VehicleServicePrice
from .forms import CategoryForm, InventoryForm, VehicleServicePriceFormSet # Import FormSet

try:
    from apps.purchases.models import PurchaseOrderItem
except ImportError:
    PurchaseOrderItem = None


# ==============================
# API VIEWS (AJAX)
# ==============================

@login_required
def get_category_specs(request, category_id):
    try:
        category = get_object_or_404(Category, id=category_id)
        if category.required_specs:
            specs_list = [s.strip() for s in category.required_specs.split(',') if s.strip()]
        else:
            specs_list = []
        return JsonResponse({'specs': specs_list})
    except Exception as e:
        return JsonResponse({'error': str(e), 'specs': []}, status=400)


# ==============================
# INVENTORY ITEM VIEWS
# ==============================

@login_required
def inventory_list(request):
    status_filter = request.GET.get('status', 'active')
    
    if status_filter == 'archived':
        items = InventoryItem.objects.filter(is_active=False)
    else:
        items = InventoryItem.objects.filter(is_active=True)

    items = items.select_related('category').annotate(usage_count=Count('transactionitem'))
    
    categories = Category.objects.filter(is_active=True).order_by('name')
    selected_category_obj = None

    query = request.GET.get('q', '')
    is_filtering = False

    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )
        is_filtering = True

    category_id = request.GET.get('category', '')
    if category_id:
        items = items.filter(category_id=category_id)
        selected_category_obj = Category.objects.filter(id=category_id).first()
        is_filtering = True

    stock_status = request.GET.get('stock_status', '')
    if stock_status == 'low':
        items = items.filter(quantity__lte=F('reorder_threshold'))
        is_filtering = True
    
    if is_filtering:
        items = items.order_by('name')
    else:
        items = items.order_by('-updated_at')

    page_number = request.GET.get('page', 1)
    paginator = Paginator(items, 20) 

    try:
        items_paginated = paginator.page(page_number)
    except PageNotAnInteger:
        items_paginated = paginator.page(1)
    except EmptyPage:
        items_paginated = paginator.page(paginator.num_pages)

    context = {
        'items': items_paginated,
        'categories': categories,
        'current_query': query,
        'current_category': int(category_id) if category_id and category_id.isdigit() else '',
        'selected_category_obj': selected_category_obj,
        'current_stock_status': stock_status,
        'current_status_tab': status_filter,
        'paginator': paginator,
    }
    return render(request, 'inventory/inventory_list.html', context)


@login_required
def inventory_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    
    # Ambil harga khusus (Modular Service Price)
    special_prices = item.service_prices.all()

    purchase_items = []
    vendor_summary = {}

    if PurchaseOrderItem:
        purchase_items = PurchaseOrderItem.objects.filter(item=item).select_related(
            'purchase_order',
            'purchase_order__vendor'
        ).order_by('-purchase_order__order_date')
        
        for po_item in purchase_items:
            vendor = po_item.purchase_order.vendor
            if vendor not in vendor_summary:
                vendor_summary[vendor] = {
                    'total_qty': 0,
                    'total_amount': 0
                }
            vendor_summary[vendor]['total_qty'] += po_item.quantity
            vendor_summary[vendor]['total_amount'] += po_item.subtotal
    
    usage_history_list = item.transactionitem_set.select_related(
        'transaction', 
        'transaction__customer', 
        'transaction__vehicle'
    ).order_by('-transaction__created_at')

    page_usage = request.GET.get('usage_page', 1)
    paginator_usage = Paginator(usage_history_list, 10)
    try:
        usage_history = paginator_usage.page(page_usage)
    except Exception:
        usage_history = paginator_usage.page(1)

    context = {
        'item': item,
        'special_prices': special_prices,
        'purchase_items': purchase_items,
        'vendor_summary': vendor_summary,
        'usage_history': usage_history,
    }
    return render(request, 'inventory/inventory_detail.html', context)


@login_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        # 🔥 Init FormSet dengan POST data
        price_formset = VehicleServicePriceFormSet(request.POST)
        
        if form.is_valid() and price_formset.is_valid():
            try:
                with transaction.atomic(): # Gunakan atomic transaction
                    item = form.save(commit=False)
                    
                    specs_data = {}
                    for key, value in request.POST.items():
                        if key.startswith('spec_'):
                            clean_key = key.replace('spec_', '')
                            if value.strip():
                                specs_data[clean_key] = value.strip()
                    
                    item.extra_specs = specs_data if specs_data else {}
                    item.save()
                    
                    # 🔥 Save FormSet (Hubungkan dengan Item yang baru dibuat)
                    prices = price_formset.save(commit=False)
                    for price in prices:
                        price.item = item
                        price.save()
                    
                    log_activity(
                        request,
                        action_type='CREATE',
                        target_model='InventoryItem',
                        target_id=item.pk,
                        details=f"Menambahkan item baru: {item.name}"
                    )
                    messages.success(request, "✅ Item berhasil ditambahkan!")
                    return redirect('inventory:inventory_list')
                    
            except Exception as e:
                messages.error(request, f"Gagal menyimpan ke database: {str(e)}")
        else:
            messages.error(request, "❌ Gagal menyimpan. Periksa input form.")
    else:
        form = InventoryForm()
        price_formset = VehicleServicePriceFormSet()

    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'price_formset': price_formset, # Kirim ke template
        'title': 'Tambah Item Baru'
    })


@login_required
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    return_to = request.GET.get('return_to', '')

    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        # 🔥 Init FormSet dengan Instance Item
        price_formset = VehicleServicePriceFormSet(request.POST, instance=item)
        return_to_post = request.POST.get('return_to', '')

        if form.is_valid() and price_formset.is_valid():
            try:
                with transaction.atomic():
                    item = form.save(commit=False)
                    
                    specs_data = {}
                    for key, value in request.POST.items():
                        if key.startswith('spec_'):
                            clean_key = key.replace('spec_', '')
                            if value.strip():
                                specs_data[clean_key] = value.strip()
                    
                    item.extra_specs = specs_data if specs_data else {}
                    item.save()
                    
                    # 🔥 Save FormSet (Termasuk delete jika ada yang dihapus)
                    price_formset.save()
                    
                    status_msg = "Non-Aktif" if not item.is_active else "Aktif"
                    log_activity(
                        request,
                        action_type='UPDATE',
                        target_model='InventoryItem',
                        target_id=item.pk,
                        details=f"Update item: {item.name}. Status: {status_msg}"
                    )

                    messages.success(request, "✅ Item berhasil diperbarui!")
                    
                    if return_to_post:
                        return redirect(return_to_post)
                    else:
                        return redirect('inventory:inventory_list')
                    
            except Exception as e:
                messages.error(request, f"Gagal update ke database: {str(e)}")
        else:
            messages.error(request, "❌ Validasi form gagal.")
    else:
        form = InventoryForm(instance=item)
        price_formset = VehicleServicePriceFormSet(instance=item)
        
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'price_formset': price_formset, # Kirim ke template
        'title': f'Edit Item: {item.name}',
        'item': item,
        'return_to': return_to
    })


# ==============================
# CATEGORY VIEWS
# ==============================

@login_required
def category_list(request):
    status = request.GET.get('status', 'active')
    
    if status == 'archived':
        categories = Category.objects.filter(is_active=False).order_by('name')
        title = "Arsip Kategori (Non-Aktif)"
    else:
        categories = Category.objects.filter(is_active=True).order_by('name')
        title = "Daftar Kategori Aktif"

    context = {
        'categories': categories,
        'current_status': status,
        'title': title
    }
    return render(request, 'inventory/category_list.html', context)


@login_required
def category_form(request, pk=None):
    if pk:
        instance = get_object_or_404(Category, pk=pk)
        title = "Edit Kategori"
        action_type = 'UPDATE'
    else:
        instance = None
        title = "Tambah Kategori"
        action_type = 'CREATE'

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=instance)
        if form.is_valid():
            cat = form.save()
            
            log_activity(
                request,
                action_type=action_type,
                target_model='Category',
                target_id=cat.pk,
                details=f"{'Mengubah' if pk else 'Membuat'} kategori: {cat.name}"
            )

            messages.success(request, f"✅ Kategori berhasil disimpan!")
            return redirect('inventory:category_list')
        else:
            messages.error(request, "Gagal menyimpan kategori.")
    else:
        form = CategoryForm(instance=instance)
        
    return render(request, 'inventory/category_form.html', {'form': form, 'title': title})