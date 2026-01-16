# apps/transactions/forms.py

from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import Transaction, TransactionItem, TransactionService
from apps.inventory.models import InventoryItem
from apps.master_data.models import Service


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['customer', 'vehicle', 'mechanic', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2-enable', 'required': True}),
            'vehicle': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'mechanic': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'value': 0}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'value': 0}),
        }


class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select', 
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1, 
                'value': 1
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0,
                'value': 0
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100,
                'value': 0
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize queryset dan tambahkan info stok di choices
        if 'item' in self.fields:
            # Ambil semua item yang aktif
            items = InventoryItem.objects.filter(is_active=True).select_related('category')
            
            # Buat choices dengan format: (id, "Nama Item (Stok: X)")
            choices = [('', 'Pilih barang...')]
            for item in items:
                # 🔥 PERBAIKAN DI SINI: ganti .stock menjadi .quantity
                stock_info = f" (Stok: {item.quantity})" if item.quantity > 0 else " (HABIS)"
                label = f"{item.name}{stock_info}"
                choices.append((item.id, label))
            
            # Set choices ke field
            self.fields['item'].choices = choices

class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={
                'class': 'form-select service-select', 
                'required': True
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1,
                'value': 1
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0,
                'value': 0
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100,
                'value': 0
            }),
        }


# --- VALIDATOR CUSTOM UNTUK FORMSET ---
class BaseTransactionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        items = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            
            cleaned_data = form.cleaned_data
            if not cleaned_data:
                continue
                
            item = cleaned_data.get('item')
            if item:
                if item in items:
                    raise ValidationError(
                        "Barang yang sama tidak boleh dipilih dua kali. "
                        "Silakan gabungkan jumlahnya."
                    )
                items.append(item)


class BaseTransactionServiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors):
            return

        services = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form):
                continue
            
            cleaned_data = form.cleaned_data
            if not cleaned_data:
                continue
                
            service = cleaned_data.get('service')
            if service:
                if service in services:
                    raise ValidationError(
                        "Jasa yang sama tidak boleh dipilih dua kali. "
                        "Silakan gabungkan jumlahnya."
                    )
                services.append(service)


# --- KONFIGURASI FORMSET ---
TransactionItemFormSet = inlineformset_factory(
    Transaction, 
    TransactionItem,
    form=TransactionItemForm,
    formset=BaseTransactionItemFormSet,
    extra=1,  # Minimal 1 form kosong
    can_delete=True
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, 
    TransactionService,
    form=TransactionServiceForm,
    formset=BaseTransactionServiceFormSet,
    extra=1,  # Minimal 1 form kosong
    can_delete=True
)