from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime, timedelta

from apps.accounts.utils import log_activity
from apps.accounts.models import CustomUser
from apps.inventory.models import InventoryItem

from .models import PurchaseOrder, Vendor
from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet


# --- LIST VIEW ---
class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 10
    ordering = ['-order_date']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vendor', 'purchaser_mechanic')
       
        query = self.request.GET.get('q')
        status = self.request.GET.get('status')
        vendor_id = self.request.GET.get('vendor')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) |
                Q(vendor__name__icontains=query) |
                Q(purchaser_mechanic__name__icontains=query) |
                Q(purchaser_custom__icontains=query)
            )
       
        if status:
            queryset = queryset.filter(status=status)
           
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                queryset = queryset.filter(order_date__range=(start_date, end_date))
            except ValueError:
                pass
           
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.all()
        context['statuses'] = PurchaseOrder.StatusChoices.choices
        
        query = self.request.GET.get('q', '')
        status_param = self.request.GET.get('status', '')
        vendor_param = self.request.GET.get('vendor')

        # Perbaikan: Pakai satu blok ini saja untuk current_vendor
        try:
            context['current_vendor'] = int(vendor_param) if vendor_param and vendor_param.isdigit() else 0
        except (ValueError, TypeError):
            context['current_vendor'] = 0
        
        context['current_query'] = query
        context['current_status'] = status_param
        # context['current_vendor'] = ... <--- HAPUS BARIS YANG INI (Redundan & Berbahaya)
        
        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')

        # Sisa kode vendor_selected dan status_selected tetap sama...
        return context

# --- DETAIL & STATUS ACTIONS ---
@login_required
def purchase_detail(request, pk):
    po = get_object_or_404(PurchaseOrder, pk=pk)
    context = {
        'po': po,
        'title': f"Detail PO-{po.id}"
    }
    return render(request, 'purchases/purchase_detail.html', context)


@login_required
def update_status(request, pk, new_status):
    """
    RULE BISNIS STATUS TRANSITION:
    - PENDING → COMPLETED ✅ (barang masuk, stok bertambah)
    - PENDING → CANCELLED ✅ (batalkan order)
    - COMPLETED → CANCELLED ✅ (kembalikan barang, cek stok dulu)
    - CANCELLED → ❌ (tidak bisa diubah lagi, final)
    - COMPLETED → PENDING ❌ (tidak masuk akal)
    """
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    # VALIDASI 1: Cek apakah status baru valid
    if new_status not in PurchaseOrder.StatusChoices.values:
        messages.error(request, "Status tidak valid.")
        return redirect('purchases:purchase_list')
    
    # VALIDASI 2: Tidak boleh ubah jika sudah CANCELLED (status final)
    if po.status == PurchaseOrder.StatusChoices.CANCELLED:
        messages.error(request, f"PO #{po.id} sudah dibatalkan. Status tidak bisa diubah lagi.")
        return redirect('purchases:purchase_list')
    
    # VALIDASI 3: Tidak boleh COMPLETED → PENDING (tidak masuk akal)
    if po.status == PurchaseOrder.StatusChoices.COMPLETED and new_status == PurchaseOrder.StatusChoices.PENDING:
        messages.error(request, "Tidak bisa mengubah status COMPLETED kembali ke PENDING.")
        return redirect('purchases:purchase_list')

    # VALIDASI 4 (BARU): Barang tidak boleh sudah dipakai di transaksi saat membatalkan
    if new_status == PurchaseOrder.StatusChoices.CANCELLED and po.has_items_used_in_transactions():
        used_items = po.get_items_used_in_transactions_detail()
        items_str = ", ".join([f"{item['item__name']} ({item['total_qty_used']} qty)" for item in used_items])
        messages.error(
            request,
            f"❌ TIDAK BISA MEMBATALKAN! Barang dari PO #{po.id} sudah dipakai di transaksi: {items_str}. "
            f"Silakan batalkan transaksi terlebih dahulu sebelum membatalkan PO."
        )
        return redirect('purchases:purchase_list')

    try:
        # Signals akan menangani logika stok otomatis
        po.status = new_status
        po.save()
       
        log_activity(request, 'UPDATE_STATUS', 'PurchaseOrder', po.pk, f"Ubah status PO #{po.pk} ke {new_status}")
        messages.success(request, f"Status PO-{po.pk} berhasil diubah menjadi {po.get_status_display()}")
           
    except ValueError as e:
        # Menangkap Error Validasi Stok dari Signals
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Gagal update status: {e}")
       
    return redirect('purchases:purchase_list')


# --- CREATE & UPDATE VIEW ---
@login_required
def purchase_form_view(request, pk=None):
    instance = get_object_or_404(PurchaseOrder, pk=pk) if pk else None
    action_type = 'UPDATE' if instance else 'CREATE'
   
    # VALIDASI EDIT: Hanya PENDING yang boleh diedit
    if instance and instance.status != PurchaseOrder.StatusChoices.PENDING:
        messages.error(request, f"PO #{instance.id} sudah diproses ({instance.get_status_display()}). Tidak bisa diedit lagi.")
        return redirect('purchases:purchase_list')

    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=instance)
        formset = PurchaseOrderItemFormSet(request.POST, instance=instance, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with db_transaction.atomic():
                    po = form.save()
                    formset.instance = po
                    formset.save()
               
                shopper = po.purchaser_mechanic.name if po.purchaser_mechanic else (po.purchaser_custom or "Admin")
                log_detail = f"{'Edit' if instance else 'Buat'} PO #{po.id} Vendor: {po.vendor.name}, Shopper: {shopper}"
               
                log_activity(request, action_type, 'PurchaseOrder', po.pk, log_detail)
               
                messages.success(request, f"Purchase Order #{po.id} berhasil disimpan.")
                return redirect('purchases:purchase_list')
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan: {e}")
        else:
            messages.error(request, "Harap perbaiki kesalahan di formulir.")
    else:
        form = PurchaseOrderForm(instance=instance)
        formset = PurchaseOrderItemFormSet(instance=instance, prefix='items')

    context = {
        'form': form,
        'formset': formset,
        'instance': instance,
        'title': f"Edit PO-{instance.id}" if instance else "Buat Purchase Order Baru"
    }
    return render(request, 'purchases/purchase_form.html', context)


# --- DELETE VIEW (UPDATED SAFETY RULES) ---
# apps/purchases/views.py

class PurchaseOrderDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_confirm_delete.html'
    success_url = reverse_lazy('purchases:purchase_list')

    def test_func(self):
        """
        ATURAN HAPUS BARU:
        1. User harus Owner.
        2. Barang dari PO ini TIDAK BOLEH sudah digunakan di transaksi.
        (Status PENDING, COMPLETED, CANCELLED boleh dihapus asal barangnya belum laku)
        """
        po = self.get_object()
        
        # 1. Cek Role Owner
        if self.request.user.role != CustomUser.RoleChoices.OWNER:
            return False

        # 2. Cek Ketergantungan Transaksi (FIFO Check)
        # Kalau sudah ada item dari PO ini yang laku, HARAM dihapus.
        if po.has_items_used_in_transactions():
            return False

        return True

    def handle_no_permission(self):
        """
        Memberikan pesan error yang spesifik kenapa ditolak.
        """
        po = self.get_object()
        
        # Kasus 1: Bukan Owner
        if self.request.user.role != CustomUser.RoleChoices.OWNER:
            messages.error(self.request, "⛔ Akses Ditolak! Hanya Owner yang boleh menghapus PO.")
        
        # Kasus 2: Barang Sudah Terpakai (Apapun status PO-nya)
        elif po.has_items_used_in_transactions():
            used_items = po.get_items_used_in_transactions_detail()
            # Perhatikan: item['name'] sesuai update di models.py
            items_str = ", ".join([f"{item['name']} ({item['total_qty_used']} qty)" for item in used_items])
            
            messages.error(
                self.request,
                f"❌ TIDAK BISA DIHAPUS! Sebagian barang dari PO #{po.id} sudah terjual: {items_str}. "
                f"Silakan batalkan transaksi penjualan terkait terlebih dahulu."
            )
        
        # Kasus Default
        else:
            messages.error(self.request, "Tidak diizinkan menghapus PO ini.")
        
        return redirect('purchases:purchase_list')

    def form_valid(self, form):
        """
        Eksekusi Hapus
        """
        po = self.object
        
        # Double check terakhir (Safety Net)
        if po.has_items_used_in_transactions():
            messages.error(self.request, "❌ Gagal! Barang dari PO ini mendadak terdeteksi sudah terjual.")
            return redirect('purchases:purchase_list')

        po_id = po.id
        vendor_name = po.vendor.name
        
        # Catat Log
        log_activity(
            self.request, 
            'DELETE', 
            'PurchaseOrder', 
            po_id, 
            f"Menghapus Permanent PO #{po_id} (Vendor: {vendor_name})"
        )
        
        # Pesan Sukses
        messages.success(
            self.request, 
            f"✅ Purchase Order #{po_id} berhasil dihapus permanen. "
            f"Stok gudang otomatis disesuaikan."
        )
        
        # Saat delete() dipanggil, signal 'pre_delete' di signals.py akan otomatis jalan
        # untuk mengurangi stok InventoryItem (jika PO tadinya COMPLETED).
        return super().form_valid(form)


# --- AUTOCOMPLETE VIEW ---
@login_required
def item_autocomplete_view(request):
    """Endpoint AJAX Select2 untuk Purchase"""
    query = request.GET.get('q', '')

    if not query:
        items = InventoryItem.objects.all().order_by('name')[:10]
    else:
        items = InventoryItem.objects.filter(
            Q(name__icontains=query) | Q(sku__icontains=query)
        ).order_by('name')[:10]

    results = [
        {
            'id': item.id,
            'text': f"{item.name} (Stok: {item.quantity})",
            'buy_price': item.buy_price,
        }
        for item in items
    ]
    return JsonResponse(results, safe=False)