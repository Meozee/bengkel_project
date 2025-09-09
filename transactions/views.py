# transactions/views.py

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Transaksi
from django.shortcuts import render, redirect
from django.utils import timezone # <-- Tambahkan import ini
from .forms import TransaksiForm # <-- Tambahkan import ini


@login_required
def transaction_list_view(request):
    # Ambil semua objek transaksi dari database, urutkan dari yang terbaru
    transactions = Transaksi.objects.all().order_by('-created_at')
    
    context = {
        'title': 'Daftar Transaksi',
        'transactions': transactions,
    }
    return render(request, 'transactions/transaction_list.html', context)

@login_required
def transaction_create_view(request):
    if request.method == 'POST':
        form = TransaksiForm(request.POST)
        if form.is_valid():
            # Jangan simpan dulu, karena kita perlu mengisi kode_transaksi
            transaksi = form.save(commit=False)
            
            # Buat kode transaksi unik sederhana berdasarkan waktu
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            transaksi.kode_transaksi = f"TRX-{timestamp}"
            
            transaksi.save()
            # Arahkan pengguna kembali ke daftar transaksi setelah berhasil
            return redirect('transaction_list')
    else:
        # Jika bukan POST, tampilkan formulir kosong
        form = TransaksiForm()
        
    context = {
        'title': 'Tambah Transaksi Baru',
        'form': form,
    }
    return render(request, 'transactions/transaction_form.html', context)