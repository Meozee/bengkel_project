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
            'customer': forms.Select(attrs={'class': 'form-select select-search'}), # Beri class untuk JS
            'vehicle': forms.Select(attrs={'class': 'form-select select-search'}),  # Beri class untuk JS
            'mechanic': forms.Select(attrs={'class': 'form-select select-search'}), # Beri class untuk JS
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
            # ✅ PERUBAHAN KRUSIAL:
            # Ganti dari HiddenInput ke Select agar bisa dipakai TomSelect.
            'item': forms.Select(attrs={'class': 'form-select item-search-input', 'placeholder': 'Cari item...'}),
            
            'quantity': forms.NumberInput(attrs={'class': 'form-control item-quantity-input', 'min': 1, 'step': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control item-price-input', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control item-discount-input', 'step': '0.01', 'min': 0, 'max': 100}),
        }

    # Hapus validasi stok di sini, kita pindahkan ke view
    # agar bisa skip validasi saat status 'PAID'
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity and quantity < 1:
            raise forms.ValidationError("Kuantitas tidak boleh kurang dari 1.")
        return quantity


class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select service-select-input select-search'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control service-quantity-input', 'min': 1, 'step': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control service-price-input', 'step': '0.01'}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control service-discount-input', 'step': '0.01', 'min': 0, 'max': 100}),
        }


# Inline formset (Tidak berubah)
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