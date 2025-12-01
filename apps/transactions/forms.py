# apps/transactions/forms.py

from django import forms
from django.forms import inlineformset_factory, NumberInput, Select, Textarea
from .models import Transaction, TransactionItem, TransactionService

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        # Kita exclude status & date karena dihandle sistem/view
        fields = ['customer', 'vehicle', 'mechanic', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            'customer': Select(attrs={'class': 'form-select select2-enable', 'required': True}),
            'vehicle': Select(attrs={'class': 'form-select select2-enable'}),
            'mechanic': Select(attrs={'class': 'form-select'}),
            'other_charges': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_amount': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'notes': Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            # Class 'item-select' penting untuk target JS Auto-fill harga
            'item': Select(attrs={'class': 'form-select item-select', 'required': True}),
            'quantity': NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            # Class 'service-select' penting untuk target JS Auto-fill harga
            'service': Select(attrs={'class': 'form-select service-select', 'required': True}),
            'quantity': NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

# --- FORMSETS CONFIGURATION ---
# can_delete=True -> Wajib agar fitur hapus saat Edit berfungsi
# extra=1 -> Menampilkan 1 baris kosong di awal (opsional, tapi bagus untuk UX)

TransactionItemFormSet = inlineformset_factory(
    Transaction, 
    TransactionItem,
    form=TransactionItemForm,
    extra=0, # Kita set 0, nanti JS yang handle add row (pake template kosong)
    can_delete=True 
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, 
    TransactionService,
    form=TransactionServiceForm,
    extra=0, 
    can_delete=True
)