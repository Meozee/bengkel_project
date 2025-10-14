from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from .models import InventoryItem, Category
from .forms import CategoryForm, InventoryForm # Impor dari forms.py

# ==============================
# INVENTORY ITEM VIEWS
# ==============================

def inventory_list(request):
    # Ambil semua item dan kategori sebagai dasar
    items = InventoryItem.objects.select_related('category').all()
    categories = Category.objects.all()

    # --- Logika Pencarian ---
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        )

    # --- Logika Filter Kategori ---
    category_id = request.GET.get('category')
    if category_id:
        items = items.filter(category_id=category_id)

    # --- Logika Filter Stok Rendah (sesuai LowStockFilter di admin) ---
    stock_status = request.GET.get('stock_status')
    if stock_status == 'low':
        items = items.filter(quantity__lte=F('reorder_threshold'))
    
    context = {
        'items': items,
        'categories': categories,
        'current_query': query or '',
        'current_category': int(category_id) if category_id else '',
        'current_stock_status': stock_status or '',
    }
    return render(request, 'inventory/inventory_list.html', context)

def inventory_detail(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    return render(request, 'inventory/inventory_detail.html', {'item': item})

def inventory_create(request):
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Item berhasil ditambahkan!")
            return redirect('inventory:inventory_list')
    else:
        # Saat membuat, disable juga field quantity dan buy_price karena harusnya 0
        form = InventoryForm(initial={'quantity': 0, 'buy_price': '0.00'})
        form.fields['quantity'].disabled = True
        form.fields['buy_price'].disabled = True

    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': 'Tambah Item Baru'
    })

def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        form = InventoryForm(request.POST, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, "Item berhasil diperbarui!")
            return redirect('inventory:inventory_list')
    else:
        form = InventoryForm(instance=item)
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': f'Edit Item: {item.name}'
    })

def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, f'Item "{item.name}" telah dihapus.')
        return redirect('inventory:inventory_list')
    return render(request, 'inventory/inventory_confirm_delete.html', {'item': item})

# ==============================
# CATEGORY VIEWS (Disederhanakan)
# ==============================

def category_list(request):
    categories = Category.objects.all()
    return render(request, 'inventory/category_list.html', {'categories': categories})

def category_form(request, pk=None):
    """Satu view untuk membuat dan mengedit kategori."""
    if pk:
        instance = get_object_or_404(Category, pk=pk)
        title = "Edit Kategori"
    else:
        instance = None
        title = "Tambah Kategori"

    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=instance)
        if form.is_valid():
            form.save()
            messages.success(request, f"Kategori berhasil disimpan!")
            return redirect('inventory:category_list')
    else:
        form = CategoryForm(instance=instance)
        
    return render(request, 'inventory/category_form.html', {'form': form, 'title': title})

def category_delete(request, pk):
    category = get_object_or_404(Category, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, "Kategori berhasil dihapus!")
        return redirect('inventory:category_list')
    return render(request, 'inventory/category_confirm_delete.html', {'category': category})