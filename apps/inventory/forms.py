from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML, Row, Column
from django.db.models import Q
from .models import InventoryItem, Category, VehicleServicePrice

class CategoryForm(forms.ModelForm):
    is_active = forms.TypedChoiceField(
        choices=[(True, 'Aktif (Digunakan)'), (False, 'Non-Aktif (Arsipkan)')],
        widget=forms.RadioSelect,
        coerce=lambda x: str(x).lower() == 'true',
        initial=True,
        label="Status Kategori"
    )

    class Meta:
        model = Category
        fields = ['name', 'description', 'required_specs', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        if not is_active and self.instance.pk:
            if self.instance.inventoryitem_set.filter(is_active=True).exists():
                raise ValidationError({
                    'is_active': "Kategori ini tidak bisa dinonaktifkan karena masih memiliki Item yang Aktif."
                })
        return cleaned_data


class InventoryForm(forms.ModelForm):
    is_active = forms.TypedChoiceField(
        choices=[(True, 'Aktif (Muncul di Sistem)'), (False, 'Non-Aktif (Diarsipkan)')],
        widget=forms.RadioSelect,
        coerce=lambda x: str(x).lower() == 'true',
        initial=True,
        label="Status Ketersediaan"
    )

    class Meta:
        model = InventoryItem
        fields = [
            'category', 'name', 'sku', 'item_type',
            'sell_price', # Install price sudah dihapus dari sini
            'reorder_threshold',
            'description', 'is_active'
        ]
        help_texts = {
            'sell_price': 'Harga barang saja (Sparepart).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        active_categories = Category.objects.filter(is_active=True).order_by('name')
        if self.instance.pk and self.instance.category and not self.instance.category.is_active:
            self.fields['category'].queryset = Category.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.category.pk)
            ).order_by('name')
        else:
            self.fields['category'].queryset = active_categories
        
        self.fields['category'].widget.attrs.update({
            'class': 'form-select select2-enable',
            'data-placeholder': 'Pilih Kategori...'
        })

        self.helper = FormHelper()
        self.helper.form_tag = False 
        self.helper.form_show_labels = True
        
        self.helper.layout = Layout(
            Field('category'),
            Field('name'),
            Row(
                Column('sku', css_class='col-md-6'),
                Column('item_type', css_class='col-md-6'),
            ),
            Field('sell_price'),
            Field('reorder_threshold'),
            Field('description', rows=3),
            Field('is_active'),
            HTML('<div id="dynamic_specs_container" class="mt-3 p-3 bg-light border rounded"></div>')
        )

    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        return sku if sku else None

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        if self.instance.pk:
            current_quantity = self.instance.quantity
            if is_active is False and current_quantity > 0:
                raise ValidationError({
                    'is_active': f"DILARANG: Stok masih ada ({current_quantity} unit). Kosongkan stok via transaksi dulu atau set manual ke 0."
                })
        return cleaned_data


# 🔥 NEW: Form untuk Detail Harga Jasa Pasang (Per Motor)
class VehicleServicePriceForm(forms.ModelForm):
    class Meta:
        model = VehicleServicePrice
        fields = ['vehicle_type', 'price']
        widgets = {
            'vehicle_type': forms.TextInput(attrs={'placeholder': 'Cth: NMAX, Beat, Sport 150cc'}),
            'price': forms.NumberInput(attrs={'placeholder': '0', 'min': 0}),
        }

# 🔥 NEW: FormSet Factory untuk Harga Jasa
VehicleServicePriceFormSet = inlineformset_factory(
    InventoryItem,
    VehicleServicePrice,
    form=VehicleServicePriceForm,
    extra=1,          # Munculkan 1 baris kosong default
    can_delete=True   # Izinkan hapus baris
)