# apps/transactions/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import Transaction, TransactionItem, TransactionService

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        # Kita HAPUS transaction_date dan status dari sini karena otomatis
        fields = ['customer', 'vehicle', 'mechanic', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2-enable', 'required': True}),
            'vehicle': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'mechanic': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control disc-input'}),
        }

class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select service-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control qty-input', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control price-input'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control disc-input'}),
        }

# Formsets
TransactionItemFormSet = inlineformset_factory(
    Transaction, TransactionItem, form=TransactionItemForm,
    extra=1, can_delete=True
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, TransactionService, form=TransactionServiceForm,
    extra=1, can_delete=True
)