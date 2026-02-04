from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError

# Import Models
from .models import Transaction, TransactionItem, TransactionService, TransactionMisc
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
            # Value 0 disini OK karena ini Single Form (Header), bukan Formset
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
                'min': 1
                # HAPUS 'value': 1 agar form kosong tidak dianggap terisi
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'item' in self.fields:
            items = InventoryItem.objects.filter(is_active=True).select_related('category')
            choices = [('', 'Pilih barang...')]
            for item in items:
                stock_info = f" (Stok: {item.quantity})" if item.quantity > 0 else " (HABIS)"
                label = f"{item.name}{stock_info}"
                choices.append((item.id, label))
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
                'min': 1
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0, 
                'max': 100
            }),
        }


class TransactionMiscForm(forms.ModelForm):
    class Meta:
        model = TransactionMisc
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama barang/biaya (Non-stok)...'
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 1
                # JANGAN PAKAI VALUE DISINI
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'min': 0
            }),
        }


# --- VALIDATOR CUSTOM UNTUK FORMSET ---
class BaseTransactionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        items = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form): continue
            cleaned_data = form.cleaned_data
            if not cleaned_data: continue
            item = cleaned_data.get('item')
            if item:
                if item in items:
                    raise ValidationError("Barang yang sama tidak boleh dipilih dua kali.")
                items.append(item)


class BaseTransactionServiceFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        services = []
        for form in self.forms:
            if self.can_delete and self._should_delete_form(form): continue
            cleaned_data = form.cleaned_data
            if not cleaned_data: continue
            service = cleaned_data.get('service')
            if service:
                if service in services:
                    raise ValidationError("Jasa yang sama tidak boleh dipilih dua kali.")
                services.append(service)


# --- KONFIGURASI FORMSET ---
TransactionItemFormSet = inlineformset_factory(
    Transaction, 
    TransactionItem,
    form=TransactionItemForm,
    formset=BaseTransactionItemFormSet,
    extra=1, 
    can_delete=True
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, 
    TransactionService,
    form=TransactionServiceForm,
    formset=BaseTransactionServiceFormSet,
    extra=1, 
    can_delete=True
)

TransactionMiscFormSet = inlineformset_factory(
    Transaction,
    TransactionMisc,
    form=TransactionMiscForm,
    extra=1, 
    can_delete=True
)