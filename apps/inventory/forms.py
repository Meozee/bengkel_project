from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, HTML, Field
from .models import InventoryItem, Category


class CategoryForm(forms.ModelForm):
    # Menggunakan TypedChoiceField agar outputnya Boolean
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
            'sell_price', 'reorder_threshold',
            'description', 'is_active'
        ]
        # Bantuan text agar user tidak bingung format harga
        help_texts = {
            'sell_price': 'Masukkan angka saja tanpa titik atau Rp (Contoh: 150000)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Logic Filter Kategori Aktif
        active_categories = Category.objects.filter(is_active=True)
        
        # 2. Logic Edit: Tetap tampilkan kategori lama meski non-aktif
        if self.instance.pk and self.instance.category and not self.instance.category.is_active:
            from django.db.models import Q
            self.fields['category'].queryset = Category.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.category.pk)
            )
        else:
            self.fields['category'].queryset = active_categories

        # 🔥 CRISPY FORMS HELPER - DEFINISI LAYOUT 🔥
        self.helper = FormHelper()
        self.helper.form_id = 'inventoryForm'
        self.helper.form_method = 'post'
        self.helper.form_show_labels = True
        
        # Layout lengkap dengan container untuk dynamic specs
        self.helper.layout = Layout(
            Field('category', css_class='form-select'),
            Field('name'),
            Field('sku'),
            Field('item_type', css_class='form-select'),
            Field('sell_price'),
            Field('reorder_threshold'),
            Field('description', rows=3),
            Field('is_active'),
            # 🔥 CONTAINER UNTUK SPESIFIKASI DINAMIS 🔥
            HTML('<div id="dynamic_specs_container" class="mt-3"></div>')
        )

    # 🔥 FIX 1: SKU Kosong dianggap NULL (Supaya tidak Error Duplicate)
    def clean_sku(self):
        sku = self.cleaned_data.get('sku')
        if not sku:  # Jika kosong string ""
            return None  # Ubah jadi None (Database membolehkan banyak NULL)
        return sku

    # 🔥 FIX 2: Bersihkan Format Harga (Hapus titik atau Rp jika user iseng ngetik)
    def clean_sell_price(self):
        price = self.cleaned_data.get('sell_price')
        # Jika form mengembalikan None (karena format salah total), biarkan error standar
        return price

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        
        # Ambil stok dari DB
        current_quantity = 0
        if self.instance.pk:
            current_quantity = self.instance.quantity
            
        # Logic Satpam Stok
        if is_active is False and current_quantity > 0:
            raise ValidationError({
                'is_active': f"DILARANG: Stok masih ada ({current_quantity} unit). Kosongkan stok via transaksi/pemakaian dulu."
            })

        return cleaned_data