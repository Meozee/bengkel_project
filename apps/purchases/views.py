from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DeleteView
from django.http import JsonResponse
from django.db import transaction as db_transaction
from django.contrib import messages
from django.db.models import Q

from .models import PurchaseOrder, Vendor
from .forms import PurchaseOrderForm, PurchaseOrderItemFormSet
from apps.inventory.models import InventoryItem

class PurchaseOrderListView(ListView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_list.html'
    context_object_name = 'purchases'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('vendor')
        query = self.request.GET.get('q')
        status = self.request.GET.get('status')
        vendor_id = self.request.GET.get('vendor')

        if query:
            queryset = queryset.filter(
                Q(id__icontains=query) | Q(vendor__name__icontains=query)
            )
        if status:
            queryset = queryset.filter(status=status)
        if vendor_id:
            queryset = queryset.filter(vendor_id=vendor_id)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['vendors'] = Vendor.objects.all()
        context['statuses'] = PurchaseOrder.StatusChoices.choices
        context['current_query'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_vendor'] = int(self.request.GET.get('vendor', 0))
        return context

def purchase_form_view(request, pk=None):
    """Satu view untuk membuat dan mengedit Purchase Order."""
    instance = get_object_or_404(PurchaseOrder, pk=pk) if pk else None
    
    if request.method == 'POST':
        form = PurchaseOrderForm(request.POST, instance=instance)
        formset = PurchaseOrderItemFormSet(request.POST, instance=instance, prefix='items')

        if form.is_valid() and formset.is_valid():
            try:
                with db_transaction.atomic():
                    purchase_order = form.save()
                    formset.instance = purchase_order
                    formset.save()
                
                messages.success(request, f"Purchase Order #{purchase_order.id} berhasil disimpan.")
                return redirect('purchases:purchase_list')
            except Exception as e:
                messages.error(request, f"Terjadi kesalahan: {e}")
        else:
            messages.error(request, "Harap perbaiki kesalahan di bawah ini.")

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

class PurchaseOrderDeleteView(DeleteView):
    model = PurchaseOrder
    template_name = 'purchases/purchase_confirm_delete.html'
    success_url = reverse_lazy('purchases:purchase_list')

    def form_valid(self, form):
        messages.success(self.request, f"Purchase Order #{self.object.id} berhasil dihapus.")
        return super().form_valid(form)

def item_autocomplete_view(request):
    """Endpoint untuk autocomplete item inventaris."""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return JsonResponse([], safe=False)

    items = InventoryItem.objects.filter(name__icontains=query)[:10]
    results = [
        {
            'id': item.id,
            'text': f"{item.name} (SKU: {item.sku or 'N/A'})",
            'buy_price': item.buy_price, # Kirim harga beli terakhir sebagai saran
        }
        for item in items
    ]
    return JsonResponse(results, safe=False)