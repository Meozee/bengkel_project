from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse 

# Import Security & Logging Custom (Asumsi file ini ada sesuai konteks sebelumnya)
from apps.accounts.utils import log_activity

from .models import InventoryItem, Category
from .forms import CategoryForm, InventoryForm

# ==============================
# API VIEWS
# ==============================

@login_required
def get_category_specs(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    if category.required_specs:
        specs_list = [s.strip() for s in category.required_specs.split(',') if s.strip()]
    else:
        specs_list = []
    return JsonResponse({'specs': specs_list})

# ==============================
# INVENTORY ITEM VIEWS
# ==============================

@login_required
def inventory_list(request):
    # ✅ FILTER UTAMA: Hanya tampilkan item yang AKTIF
    items = InventoryItem.objects.filter(is_active=True).select_related('category')
    
    # ✅ FILTER KATEGORI: Hanya tampilkan kategori yang AKTIF
    categories = Category.objects.filter(is_active=True)
    selected_category_obj = None

    # 1. Filter Pencarian Teks
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    # 2. Filter Kategori
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)
        selected_category_obj = Category.objects.filter(id=category_id).first()

    # 3. Filter Status Stok
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        items = items.filter(quantity__lte=F('reorder_threshold'))
    
    context = {
        'items': items,
        'categories': categories,
        'current_query': query or '',
        'current_category': int(category_id) if category_id and category_id.isdigit() else '',
        'selected_category_obj': selected_category_obj,
        'current_stock_status': stock_status or '',
    }
    return render(request, 'inventory/inventory_list.html', context)


@login_required
def inventory_detail(request, pk):
    # Detail tetap bisa diakses meskipun non-aktif (untuk keperluan audit via URL langsung)
    # Tapi kalau mau restrict, bisa tambah filter(is_active=True)
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, 'inventory/inventory_detail.html', {'item': item})


@login_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            item = form.save() 
            
            log_activity(
                request, 
                action_type='CREATE', 
                target_model='InventoryItem', 
                target_id=item.pk, 
                details=f"Menambahkan item baru: {item.name}"
            )
            
            messages.success(request, "Item berhasil ditambahkan!")
            return redirect('inventory:inventory_list')
    else:
        form = InventoryForm() 

    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': 'Tambah Item Baru'
    })


@login_required
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        
        # Validasi "Satpam" stok ada di forms.py -> clean()
        # Jadi kita cukup cek form.is_valid()
        if form.is_valid():
            item = form.save()
            
            # Cek status untuk logging yang lebih jelas
            status_msg = "Non-Aktif" if not item.is_active else "Aktif"
            
            log_activity(
                request, 
                action_type='UPDATE', 
                target_model='InventoryItem', 
                target_id=item.pk, 
                details=f"Update item: {item.name}. Status sekarang: {status_msg}"
            )

            messages.success(request, "Item berhasil diperbarui!")
            return redirect('inventory:inventory_list')
    else:
        form = InventoryForm(instance=item)
        
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': f'Edit Item: {item.name}'
    })

# ❌ VIEW DELETE SUDAH DIHAPUS 
# Karena logic pindah ke inventory_update via status is_active

# ==============================
# CATEGORY VIEWS
# ==============================

@login_required
def category_list(request):
    # ✅ Filter hanya kategori aktif
    categories = Category.objects.filter(is_active=True)
    return render(request, 'inventory/category_list.html', {'categories': categories})


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

            messages.success(request, f"Kategori berhasil disimpan!")
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=instance)
        
    return render(request, 'inventory/category_form.html', {'form': form, 'title': title})

# ❌ VIEW CATEGORY DELETE SUDAH DIHAPUS