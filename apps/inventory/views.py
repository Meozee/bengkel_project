# apps/inventory/views.py

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse 

# Import Security & Logging Custom kita
from apps.accounts.decorators import owner_required
from apps.accounts.utils import log_activity

from .models import InventoryItem, Category
from .forms import CategoryForm, InventoryForm

# ==============================
# API VIEWS (Untuk JavaScript)
# ==============================

@login_required
def get_category_specs(request, category_id):
    """
    API untuk mengambil daftar spesifikasi kategori.
    Digunakan oleh JavaScript di form inventory.
    """
    category = get_object_or_404(Category, id=category_id)
    
    if category.required_specs:
        # Pecah string "Volume, SAE" menjadi list ['Volume', 'SAE']
        # Gunakan strip() untuk menghapus spasi berlebih
        specs_list = [s.strip() for s in category.required_specs.split(',') if s.strip()]
    else:
        specs_list = []
    
    return JsonResponse({'specs': specs_list})

# ==============================
# INVENTORY ITEM VIEWS
# ==============================

@login_required
def inventory_list(request):
    items = InventoryItem.objects.select_related('category').all()
    categories = Category.objects.all()
    selected_category_obj = None

    # 1. Filter Pencarian Teks
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    # 2. Filter Kategori (Dirapikan)
    category_id = request.GET.get('category')
    if category_id:
        # Filter items berdasarkan kategori
        items = items.filter(category_id=category_id)
        # Ambil objek kategori untuk keperluan tampilan tabel dinamis
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
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, 'inventory/inventory_detail.html', {'item': item})


@login_required
def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            item = form.save() 
            
            # --- LOG ACTIVITY ---
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
        if form.is_valid():
            item = form.save()
            
            # --- LOG ACTIVITY ---
            log_activity(
                request, 
                action_type='UPDATE', 
                target_model='InventoryItem', 
                target_id=item.pk, 
                details=f"Mengupdate detail item: {item.name}"
            )

            messages.success(request, "Item berhasil diperbarui!")
            return redirect('inventory:inventory_list')
    else:
        form = InventoryForm(instance=item)
        
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': f'Edit Item: {item.name}'
    })


@owner_required 
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item_name = item.name
        item_pk = item.pk
        
        item.delete()
        
        # --- LOG ACTIVITY ---
        log_activity(
            request, 
            action_type='DELETE', 
            target_model='InventoryItem', 
            target_id=item_pk, 
            details=f"Menghapus permanent item: {item_name}"
        )

        messages.success(request, f'Item "{item_name}" telah dihapus.')
        return redirect('inventory:inventory_list')
    return render(request, 'inventory/inventory_confirm_delete.html', {'item': item})

# ==============================
# CATEGORY VIEWS
# ==============================

@login_required
def category_list(request):
    categories = Category.objects.all()
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
            
            # --- LOG ACTIVITY ---
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


@owner_required
def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        cat_name = category.name
        cat_pk = category.pk
        
        category.delete()
        
        # --- LOG ACTIVITY ---
        log_activity(
            request, 
            action_type='DELETE', 
            target_model='Category', 
            target_id=cat_pk, 
            details=f"Menghapus kategori: {cat_name}"
        )

        messages.success(request, "Kategori berhasil dihapus!")
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})