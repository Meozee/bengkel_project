# ===== apps/transactions/forms.py =====
from django import forms
from django.forms import inlineformset_factory
from .models import Transaction, TransactionItem, TransactionService
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['invoice_number', 'customer', 'vehicle', 'mechanic', 'status', 
                 'transaction_date', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            'invoice_number': forms.TextInput(attrs={'class': 'form-control'}),
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'vehicle': forms.Select(attrs={'class': 'form-select'}),
            'mechanic': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'transaction_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }


class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.HiddenInput(),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        item = self.cleaned_data.get('item')

        # Skip validasi jika transaksi sudah PAID (edit mode)
        if self.instance.pk and self.instance.transaction.status == 'PAID':
            return quantity

        if item and quantity > item.quantity:
            raise forms.ValidationError(f"Stok tidak cukup untuk {item.name}. Sisa stok: {item.quantity}.")
        return quantity


class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100}),
        }


# Inline formset
TransactionItemFormSet = inlineformset_factory(
    Transaction, TransactionItem,
    form=TransactionItemForm,
    extra=1,
    can_delete=True
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, TransactionService,
    form=TransactionServiceForm,
    extra=1,
    can_delete=True
)
