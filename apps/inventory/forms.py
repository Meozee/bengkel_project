from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field, HTML
from django.db.models import Q
from .models import InventoryItem, Category

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
            'sell_price', 'reorder_threshold',
            'description', 'is_active'
        ]
        help_texts = {
            'sell_price': 'Masukkan angka saja (Contoh: 150000).',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # 1. Filter Kategori: Tampilkan yang aktif saja, KECUALI sedang edit item lama yg kategorinya non-aktif
        active_categories = Category.objects.filter(is_active=True)
        if self.instance.pk and self.instance.category and not self.instance.category.is_active:
            self.fields['category'].queryset = Category.objects.filter(
                Q(is_active=True) | Q(pk=self.instance.category.pk)
            )
        else:
            self.fields['category'].queryset = active_categories

        # 🔥 CRISPY FORMS SETUP 🔥
        self.helper = FormHelper()
        
        # ✅ SOLUSI FIX SAVE: 
        # Kita set False agar Crispy TIDAK membuat tag <form> sendiri.
        # Karena kita sudah buat tag <form> manual di HTML.
        self.helper.form_tag = False 
        
        self.helper.form_show_labels = True
        
        # Layout Field
        self.helper.layout = Layout(
            Field('category', css_class='form-select'),
            Field('name'),
            Field('sku'),
            Field('item_type', css_class='form-select'),
            Field('sell_price'),
            Field('reorder_threshold'),
            Field('description', rows=3),
            Field('is_active'),
            
            # Container kosong untuk script JS mengisi spesifikasi
            HTML('<div id="dynamic_specs_container" class="mt-3 p-3 bg-light border rounded"></div>')
        )

    def clean_sku(self):
        """Ubah string kosong menjadi None agar tidak error Unique Constraint di DB"""
        sku = self.cleaned_data.get('sku')
        if not sku:
            return None
        return sku

    def clean_sell_price(self):
        """Membersihkan input harga dari karakter non-angka"""
        price = self.cleaned_data.get('sell_price')
        # Jika user iseng input, biarkan Django handle error validasi standard
        return price

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active')
        
        # Validasi logika bisnis: Tidak boleh non-aktif jika stok masih ada
        if self.instance.pk:
            current_quantity = self.instance.quantity
            if is_active is False and current_quantity > 0:
                raise ValidationError({
                    'is_active': f"DILARANG: Stok masih ada ({current_quantity} unit). Kosongkan stok via transaksi dulu."
                })
        return cleaned_data