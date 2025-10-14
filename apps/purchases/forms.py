from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['vendor', 'order_date', 'expected_delivery_date', 'status', 'notes']
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'quantity', 'unit_price']
        widgets = {
            # Kita akan ganti ini dengan input teks untuk autocomplete di template
            'item': forms.Select(attrs={'class': 'form-select item-select'}), 
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

# Membuat inline formset untuk item-item dalam Purchase Order
PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1, # Jumlah form kosong yang ditampilkan
    can_delete=True, # Izinkan penghapusan item
    can_delete_extra=True
)