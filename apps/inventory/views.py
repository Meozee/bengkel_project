from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Q, F
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json

# Import Security & Logging Custom
try:
    from apps.accounts.utils import log_activity
except ImportError:
    # Fallback jika utils belum ada
    def log_activity(request, **kwargs):
        pass

# Import Models Inventory
from .models import InventoryItem, Category
from .forms import CategoryForm, InventoryForm

# Import Model dari App Purchases
try:
    from apps.purchases.models import PurchaseOrderItem
except ImportError:
    PurchaseOrderItem = None


# ==============================
# API VIEWS (AJAX)
# ==============================

@login_required
def get_category_specs(request, category_id):
    """API untuk mengambil daftar spesifikasi wajib berdasarkan kategori"""
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
    """
    Menampilkan daftar barang.
    LOGIC: Hanya menampilkan item yang STATUS-nya AKTIF (Soft Delete aman).
    """
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
    """
    Menampilkan detail barang LENGKAP dengan riwayat pembelian (PO).
    """
    item = get_object_or_404(InventoryItem, pk=pk)
    
    purchase_items = []
    vendor_summary = {}

    # --- LOGIKA: AMBIL RIWAYAT PEMBELIAN ---
    if PurchaseOrderItem:
        purchase_items = PurchaseOrderItem.objects.filter(item=item).select_related(
            'purchase_order',
            'purchase_order__vendor'
        ).order_by('-purchase_order__order_date')
        
        # --- LOGIKA: HITUNG RINGKASAN PER VENDOR ---
        for po_item in purchase_items:
            vendor = po_item.purchase_order.vendor
            if vendor not in vendor_summary:
                vendor_summary[vendor] = {
                    'total_qty': 0,
                    'total_amount': 0
                }
            vendor_summary[vendor]['total_qty'] += po_item.quantity
            vendor_summary[vendor]['total_amount'] += po_item.subtotal
    
    context = {
        'item': item,
        'purchase_items': purchase_items,
        'vendor_summary': vendor_summary,
    }
    return render(request, 'inventory/inventory_detail.html', context)


@login_required
def inventory_create(request):
    if request.method == 'POST':
        print("=" * 60)
        print("📥 POST REQUEST DITERIMA")
        print("=" * 60)
        print("POST Data:", dict(request.POST))
        print("=" * 60)
        
        form = InventoryForm(request.POST)
        
        if form.is_valid():
            print("✅ FORM VALID!")
            
            # 1. Pause saving (jangan commit ke DB dulu)
            item = form.save(commit=False)
            
            # 2. 🔥 LOGIKA JSON SPESIFIKASI 🔥
            specs_data = {}
            for key, value in request.POST.items():
                if key.startswith('spec_'):
                    clean_key = key.replace('spec_', '')
                    if value.strip():
                        specs_data[clean_key] = value.strip()
            
            print(f"📦 Specs Data: {specs_data}")
            
            # Masukkan ke field JSON di model
            item.extra_specs = specs_data if specs_data else {}
            
            # 3. Save beneran ke DB
            try:
                item.save()
                print(f"✅ BERHASIL SAVE! Item ID: {item.pk}")
                
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
                print(f"❌ ERROR SAAT SAVE: {str(e)}")
                messages.error(request, f"Gagal menyimpan ke database: {str(e)}")
        else:
            # ❌ FORM TIDAK VALID
            print("=" * 60)
            print("❌ FORM TIDAK VALID!")
            print("=" * 60)
            print("Form Errors (JSON):", form.errors.as_json())
            print("=" * 60)
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
                messages.error(request, f"Error di field '{field}': {errors}")
            print("=" * 60)
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
        print("=" * 60)
        print(f"📝 UPDATE REQUEST untuk Item ID: {pk}")
        print("=" * 60)
        print("POST Data:", dict(request.POST))
        print("=" * 60)
        
        form = InventoryForm(request.POST, instance=item)
        
        if form.is_valid():
            print("✅ FORM VALID!")
            
            item = form.save(commit=False)
            
            # --- LOGIKA UPDATE SPEC (SAMA SEPERTI CREATE) ---
            specs_data = {}
            for key, value in request.POST.items():
                if key.startswith('spec_'):
                    clean_key = key.replace('spec_', '')
                    if value.strip():
                        specs_data[clean_key] = value.strip()
            
            print(f"📦 Specs Data: {specs_data}")
            item.extra_specs = specs_data if specs_data else {}
            
            try:
                item.save()
                print(f"✅ BERHASIL UPDATE! Item ID: {item.pk}")
                
                status_msg = "Non-Aktif" if not item.is_active else "Aktif"
                log_activity(
                    request,
                    action_type='UPDATE',
                    target_model='InventoryItem',
                    target_id=item.pk,
                    details=f"Update item: {item.name}. Status sekarang: {status_msg}"
                )

                messages.success(request, "✅ Item berhasil diperbarui!")
                return redirect('inventory:inventory_list')
            except Exception as e:
                print(f"❌ ERROR SAAT UPDATE: {str(e)}")
                messages.error(request, f"Gagal update ke database: {str(e)}")
        else:
            print("=" * 60)
            print("❌ FORM TIDAK VALID!")
            print("=" * 60)
            print("Form Errors (JSON):", form.errors.as_json())
            print("=" * 60)
            for field, errors in form.errors.items():
                print(f"Field '{field}': {errors}")
                messages.error(request, f"Error di field '{field}': {errors}")
            print("=" * 60)
    else:
        form = InventoryForm(instance=item)
        
    return render(request, 'inventory/inventory_form.html', {
        'form': form,
        'title': f'Edit Item: {item.name}'
    })


# ==============================
# CATEGORY VIEWS
# ==============================

@login_required
def category_list(request):
    status = request.GET.get('status', 'active')
    
    if status == 'archived':
        categories = Category.objects.filter(is_active=False)
        title = "Arsip Kategori (Non-Aktif)"
    else:
        categories = Category.objects.filter(is_active=True)
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
            print("❌ ERROR CATEGORY FORM:", form.errors)
            messages.error(request, "Gagal menyimpan kategori.")
    else:
        form = CategoryForm(instance=instance)
        
    return render(request, 'inventory/category_form.html', {'form': form, 'title': title})