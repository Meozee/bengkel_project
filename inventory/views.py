# inventory/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from users.decorators import role_required
from .models import Produk, Merek, Kategori, Supplier
from .forms import ProdukForm
from django.contrib import messages
from django.utils import timezone
from core.models import ActivityLog # <-- Impor ActivityLog dari core

@login_required
@role_required(allowed_roles=['admin', 'staff'])
def inventory_dashboard_view(request):
    context = {
        'title': 'Manajemen Inventaris',
        'produks': Produk.objects.all().order_by('nama_produk'),
        'mereks': Merek.objects.all(),
        'kategoris': Kategori.objects.all(),
        'suppliers': Supplier.objects.all(),
        # PERBAIKAN: Gunakan ActivityLog, bukan LogAktivitas
        'logs': ActivityLog.objects.all()[:20] 
    }
    return render(request, 'inventory/inventory_dashboard.html', context)


# --- CRUD untuk Produk ---
@login_required
@role_required(allowed_roles=['admin', 'staff'])
def produk_create_view(request):
    form = ProdukForm(request.POST or None)
    if form.is_valid():
        produk = form.save()
        LogAktivitas.objects.create(
            produk=produk,
            action='CREATE',
            detail=f"Produk '{produk.nama_produk}' dibuat",
            user=request.user
        )
        messages.success(request, "Produk berhasil ditambahkan.")
        return redirect('inventory:inventory_dashboard')
    context = {'title': 'Tambah Produk Baru', 'form': form}
    return render(request, 'inventory/produk_form.html', context)


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def produk_update_view(request, pk):
    produk = get_object_or_404(Produk, pk=pk)
    form = ProdukForm(request.POST or None, instance=produk)
    if form.is_valid():
        old_data = f"Produk '{produk.nama_produk}' diubah"
        produk = form.save()
        LogAktivitas.objects.create(
            produk=produk,
            action='UPDATE',
            detail=old_data,
            user=request.user
        )
        messages.success(request, "Produk berhasil diperbarui.")
        return redirect('inventory:inventory_dashboard')
    context = {'title': f'Edit Produk: {produk.nama_produk}', 'form': form}
    return render(request, 'inventory/produk_form.html', context)


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def produk_delete_view(request, pk):
    item = get_object_or_404(Produk, pk=pk)
    if request.method == 'POST':
        LogAktivitas.objects.create(
            produk=item,
            action='DELETE',
            detail=f"Produk '{item.nama_produk}' dihapus",
            user=request.user
        )
        item.delete()
        messages.success(request, "Produk berhasil dihapus.")
        return redirect('inventory:inventory_dashboard')
    return render(request, 'users/confirm_delete.html', {'item': item})


# --- CRUD untuk Data Master ---
@login_required
@role_required(allowed_roles=['admin', 'staff'])
def merek_create_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        if nama:
            Merek.objects.create(nama=nama)
            messages.success(request, "Merek berhasil ditambahkan.")
    return redirect('inventory:inventory_dashboard')


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def merek_delete_view(request, pk):
    item = get_object_or_404(Merek, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Merek berhasil dihapus.")
    return redirect('inventory:inventory_dashboard')


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def kategori_create_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        if nama:
            Kategori.objects.create(nama=nama)
            messages.success(request, "Kategori berhasil ditambahkan.")
    return redirect('inventory:inventory_dashboard')


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def kategori_delete_view(request, pk):
    item = get_object_or_404(Kategori, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Kategori berhasil dihapus.")
    return redirect('inventory:inventory_dashboard')


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def supplier_create_view(request):
    if request.method == 'POST':
        nama = request.POST.get('nama')
        kontak = request.POST.get('kontak')
        alamat = request.POST.get('alamat')
        if nama:
            Supplier.objects.create(nama=nama, kontak=kontak, alamat=alamat)
            messages.success(request, "Supplier berhasil ditambahkan.")
    return redirect('inventory:inventory_dashboard')


@login_required
@role_required(allowed_roles=['admin', 'staff'])
def supplier_delete_view(request, pk):
    item = get_object_or_404(Supplier, pk=pk)
    if request.method == 'POST':
        item.delete()
        messages.success(request, "Supplier berhasil dihapus.")
    return redirect('inventory:inventory_dashboard')