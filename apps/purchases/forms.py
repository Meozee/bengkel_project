# apps/purchases/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'vendor', 'order_date', 'status', 
            'purchaser_mechanic', 'purchaser_custom', # <-- Field Baru
            'expected_delivery_date', 'notes'
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select select2-enable'}), # Tambah class select2
            'order_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            
            'purchaser_mechanic': forms.Select(attrs={'class': 'form-select', 'data-placeholder': 'Pilih Montir (Opsional)'}),
            'purchaser_custom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Atau ketik nama pembeli lain...'}),
            
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'quantity', 'unit_price']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}), 
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1, 
    can_delete=True,
    can_delete_extra=True
)