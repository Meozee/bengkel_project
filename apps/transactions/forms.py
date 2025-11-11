from django import forms
from django.forms import inlineformset_factory
from .models import Transaction, TransactionItem, TransactionService
from apps.master_data.models import Customer, Vehicle, Mechanic, Service
from apps.inventory.models import InventoryItem


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = [
            'customer', 'vehicle', 'mechanic', 'transaction_date',
            'status', 'other_charges', 'discount_amount', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'vehicle': forms.Select(attrs={
                'class': 'form-select',
            }),
            'mechanic': forms.Select(attrs={
                'class': 'form-select',
            }),
            'transaction_date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'other_charges': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'discount_amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'value': '0'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial datetime format
        if self.instance and self.instance.transaction_date:
            self.initial['transaction_date'] = self.instance.transaction_date.strftime('%Y-%m-%dT%H:%M')


class TransactionItemForm(forms.ModelForm):
    # Field khusus untuk search item (tidak disimpan ke database)
    item_search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control item-search',
            'placeholder': 'Cari item...'
        })
    )
    
    class Meta:
        model = TransactionItem
        fields = ['item', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control unit-price',
                'step': '0.01',
                'min': '0'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
        }


class TransactionServiceForm(forms.ModelForm):
    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'service': forms.Select(attrs={
                'class': 'form-select service-select',
            }),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'value': '1'
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control service-price',
                'step': '0.01',
                'min': '0'
            }),
            'discount_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'max': '100',
                'value': '0'
            }),
        }


# Formset untuk items (barang)
TransactionItemFormSet = inlineformset_factory(
    Transaction,
    TransactionItem,
    form=TransactionItemForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)

# Formset untuk services (jasa)
TransactionServiceFormSet = inlineformset_factory(
    Transaction,
    TransactionService,
    form=TransactionServiceForm,
    extra=1,
    can_delete=True,
    min_num=0,
    validate_min=False
)