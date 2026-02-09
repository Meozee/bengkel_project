from django import forms
from django.forms import inlineformset_factory, BaseInlineFormSet, ModelChoiceField
from django.core.exceptions import ValidationError
# Import helper untuk format angka ribuan di dropdown
from django.contrib.humanize.templatetags.humanize import intcomma

# Import Models
from .models import Transaction, TransactionItem, TransactionService, TransactionMisc
from apps.inventory.models import InventoryItem, VehicleServicePrice
from apps.master_data.models import Service, Vehicle, Customer, Mechanic

# --- CUSTOM FIELD: Agar dropdown Jasa Service muncul Harga ---
class ServiceModelChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.name} - Rp {intcomma(obj.price)}"

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['customer', 'vehicle', 'mechanic', 'other_charges', 'discount_amount', 'notes']
        widgets = {
            # Hapus 'required' di widget agar validasi browser tidak mengganggu formset hidden fields
            'customer': forms.Select(attrs={'class': 'form-select select2-enable'}), 
            'vehicle': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'mechanic': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'other_charges': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_amount': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sort Dropdown A-Z
        self.fields['vehicle'].queryset = Vehicle.objects.all().order_by('license_plate')
        self.fields['customer'].queryset = Customer.objects.all().order_by('name')
        self.fields['mechanic'].queryset = Mechanic.objects.all().order_by('name')


class TransactionItemForm(forms.ModelForm):
    class Meta:
        model = TransactionItem
        # Menggunakan 'install_service' (ForeignKey) bukan include_install (Boolean)
        fields = ['item', 'install_service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'item': forms.Select(attrs={
                'class': 'form-select item-select', 
            }),
            'install_service': forms.Select(attrs={
                'class': 'form-select install-select',
                'title': 'Pilih jenis jasa pasang (opsional)'
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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'item' in self.fields:
            # Dropdown Item: Tampilkan nama + info stok, urut abjad
            items = InventoryItem.objects.filter(is_active=True).select_related('category').order_by('name')
            choices = [('', 'Pilih barang...')]
            for item in items:
                stock_info = f" (Stok: {item.quantity})" if item.quantity > 0 else " (HABIS)"
                label = f"{item.name}{stock_info}"
                choices.append((item.id, label))
            self.fields['item'].choices = choices
        
        if 'install_service' in self.fields:
            # Dropdown Jasa Pasang: Default ambil semua, nanti difilter via JS di frontend
            self.fields['install_service'].queryset = VehicleServicePrice.objects.all()
            self.fields['install_service'].empty_label = "Tanpa Pasang"


class TransactionServiceForm(forms.ModelForm):
    # Custom Field agar dropdown menampilkan harga
    service = ServiceModelChoiceField(
        queryset=Service.objects.none(), # Diisi di __init__
        widget=forms.Select(attrs={'class': 'form-select service-select'}),
        empty_label="Pilih Jasa..."
    )

    class Meta:
        model = TransactionService
        fields = ['service', 'quantity', 'unit_price', 'discount_percentage']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'service' in self.fields:
            self.fields['service'].queryset = Service.objects.all().order_by('name')


class TransactionMiscForm(forms.ModelForm):
    class Meta:
        model = TransactionMisc
        fields = ['description', 'quantity', 'unit_price']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nama barang/biaya (Non-stok)...'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


# --- FORMSET VALIDATORS ---
class BaseTransactionItemFormSet(BaseInlineFormSet):
    def clean(self):
        super().clean()
        if any(self.errors): return
        # Logic validasi tambahan bisa ditaruh di sini jika perlu

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


# --- CONFIGURATION FORMSET ---
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