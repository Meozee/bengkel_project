# apps/inventory/forms.py

from django import forms
from .models import InventoryItem, Category
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset

class CategoryForm(forms.ModelForm):
    """
    Form untuk Kategori. Sederhana dan tidak ada masalah.
    """
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # Kita atur tombol submit manual di template
        self.helper.form_tag = False 


class InventoryForm(forms.ModelForm):
    """
    Form untuk mengedit detail item.
    Stok dan Harga Beli (quantity & buy_price) SENGAJA DIHAPUS
    dari form ini agar tidak divalidasi dan tidak bisa diedit.
    """
    class Meta:
        model = InventoryItem
        
        # PERHATIKAN: 'quantity' dan 'buy_price' TIDAK ADA di daftar ini.
        # Ini adalah solusi finalnya.
        fields = [
            'name', 'sku', 'category', 'item_type', 
            'description', 
            'sell_price', 
            'reorder_threshold'
        ]
        
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hapus semua logika 'readonly'/'disabled' dari sini.
        # Form ini sekarang bersih dan hanya mengurus field di atas.

        # --- Pengaturan Crispy Forms ---
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        # Kita nonaktifkan form_tag agar bisa gabung di <form> template
        self.helper.form_tag = False 
        
        # Layout ini sekarang HANYA merender field yang bisa diedit
        self.helper.layout = Layout(
            Fieldset(
                'Informasi Item',
                Row(
                    Column('name', css_class='form-group col-md-6 mb-3'),
                    Column('sku', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-3'),
                    Column('item_type', css_class='form-group col-md-6 mb-3'),
                ),
                'description',
                css_class='border p-3 rounded mb-3'
            ),
            
            Fieldset(
                'Informasi Harga & Stok (Yang Bisa Diedit)',
                Row(
                    Column('sell_price', css_class='form-group col-md-6 mb-3'),
                    Column('reorder_threshold', css_class='form-group col-md-6 mb-3'),
                ),
                css_class='border p-3 rounded mb-3'
            )
        )