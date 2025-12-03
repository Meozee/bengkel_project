from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet
from django.core.exceptions import ValidationError
from .models import Transaction, TransactionItem, TransactionService

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['customer', 'vehicle', 'mechanic', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2-enable', 'required': True}),
            'vehicle': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'mechanic': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select', 'required': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={'class': 'form-select service-select', 'required': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
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
                    raise ValidationError("Barang yang sama tidak boleh dipilih dua kali. Silakan gabungkan jumlahnya.")
                items.append(item)

# --- KONFIGURASI FORMSET ---
TransactionItemFormSet = inlineformset_factory(
    Transaction, TransactionItem,
    form=TransactionItemForm,
    formset=BaseTransactionItemFormSet, # Pasang validator di sini
    extra=0, can_delete=True
)

TransactionServiceFormSet = inlineformset_factory(
    Transaction, TransactionService,
    form=TransactionServiceForm,
    extra=0, can_delete=True
)