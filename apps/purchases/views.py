# apps/purchases/views.py

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

# Tools
from apps.accounts.utils import log_activity
from apps.accounts.models import CustomUser

from .models import PurchaseOrder, Vendor
from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet
from apps.inventory.models import InventoryItem

class PurchaseOrderListView(LoginRequiredMixin, ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 10
    ordering = ['-order_date']

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vendor', 'purchaser_mechanic')
        
        # Ambil Parameter Filter
        query = self.request.GET.get('q')
        status = self.request.GET.get('status')
        vendor_id = self.request.GET.get('vendor')
        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        # 1. Filter Keyword (ID, Vendor, atau Nama Pembeli)
        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) | 
                Q(vendor__name__icontains=query) |
                Q(purchaser_mechanic__name__icontains=query) |
                Q(purchaser_custom__icontains=query)
            )
        
        # 2. Filter Status
        if status:
            queryset = queryset.filter(status=status)
            
        # 3. Filter Vendor
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)

        # 4. Filter Tanggal (Range)
        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                # Set end date ke akhir hari (23:59:59)
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d') + timedelta(days=1) - timedelta(seconds=1)
                queryset = queryset.filter(order_date__range=(start_date, end_date))
            except ValueError:
                pass # Abaikan jika format tanggal salah
            
        return queryset

   # apps/purchases/views.py

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.all()
        context['statuses'] = PurchaseOrder.StatusChoices.choices
        
        # Kirim kembali nilai filter ke template agar input tidak reset
        context['current_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        
        # --- PERBAIKAN UTAMA ADA DISINI ---
        # Cek dulu apakah vendor_param ada isinya sebelum di-convert ke int
        vendor_param = self.request.GET.get('vendor')
        context['current_vendor'] = int(vendor_param) if vendor_param else ''
        # ----------------------------------

        context['start_date'] = self.request.GET.get('start_date', '')
        context['end_date'] = self.request.GET.get('end_date', '')
        return context


# --- VIEW BARU: DETAIL PO ---
@login_required
def purchase_detail(request, pk):
    """Melihat rincian Purchase Order."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    context = {
        'po': po,
        'title': f"Detail PO-{po.id}"
    }
    return render(request, 'purchases/purchase_detail.html', context)

# --- VIEW BARU: QUICK STATUS UPDATE ---
@login_required
def update_status(request, pk, new_status):
    """Mengubah status PO langsung dari List."""
    po = get_object_or_404(PurchaseOrder, pk=pk)
    
    if new_status not in PurchaseOrder.StatusChoices.values:
        messages.error(request, "Status tidak valid.")
        return redirect('purchases:purchase_list')

    try:
        # Logic stok sudah di-handle oleh signals.py saat save()
        po.status = new_status
        po.save() 
        
        log_activity(request, 'UPDATE_STATUS', 'PurchaseOrder', po.pk, f"Ubah status PO #{po.pk} ke {new_status}")
        messages.success(request, f"Status PO-{po.pk} berhasil diubah menjadi {po.get_status_display()}")
            
    except Exception as e:
        messages.error(request, f"Gagal update status: {e}")
        
    return redirect('purchases:purchase_list')
    
@login_required
def purchase_form_view(request, pk=None):
    """View untuk Create dan Edit PO."""
    instance = get_object_or_404(PurchaseOrder, pk=pk) if pk else None
    action_type = 'UPDATE' if instance else 'CREATE'
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=instance)
        formset = PurchaseOrderItemFormSet(request.POST, instance=instance, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with db_transaction.atomic():
                    po = form.save()
                    formset.instance = po
                    formset.save()
                
                # Logging Detail (Sertakan nama pembeli)
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

class PurchaseOrderDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_confirm_delete.html'
    success_url = reverse_lazy('purchases:purchase_list')

    # Security: Hanya Owner
    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER
    
    def handle_no_permission(self):
        messages.error(self.request, "Akses Ditolak! Hanya Owner yang boleh menghapus PO.")
        return redirect('purchases:purchase_list')

    def form_valid(self, form):
        po_id = self.object.id
        vendor = self.object.vendor.name
        log_activity(self.request, 'DELETE', 'PurchaseOrder', po_id, f"Hapus PO #{po_id} (Vendor: {vendor})")
        messages.success(self.request, f"Purchase Order #{po_id} berhasil dihapus.")
        return super().form_valid(form)

@login_required
def item_autocomplete_view(request):
    """Endpoint AJAX Select2.

    Jika parameter `q` kosong, kembalikan top-10 item sehingga Select2 dapat
    menampilkan opsi ketika dropdown dibuka tanpa mengetik. Jika ada query,
    lakukan pencarian seperti biasa.
    """
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