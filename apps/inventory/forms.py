# apps/inventory/forms.py (VERSI FINAL)

from django import forms
from .models import InventoryItem, Category
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Fieldset, HTML 

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        # KEMBALIKAN required_specs
        fields = ['name', 'description', 'required_specs'] 
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'required_specs': forms.TextInput(attrs={'placeholder': 'Contoh: Volume, SAE, Warna (Pisahkan dengan koma)'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False

# ... (InventoryForm sama persis dengan yang di langkah 1)
class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'sku', 'category', 'item_type', 
            'description', 'sell_price', 'reorder_threshold'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        
        self.helper.layout = Layout(
            Fieldset(
                'Informasi Item',
                Row(
                    Column('name', css_class='form-group col-md-6 mb-3'),
                    Column('sku', css_class='form-group col-md-6 mb-3'),
                ),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-3', id='id_category_wrapper'),
                    Column('item_type', css_class='form-group col-md-6 mb-3'),
                ),
                'description',
                css_class='border p-3 rounded mb-3'
            ),
            Fieldset(
                'Spesifikasi Khusus',
                HTML('<div id="dynamic_specs_container"></div>'),
                css_class='border p-3 rounded mb-3'
            ),
            Fieldset(
                'Harga & Stok',
                Row(
                    Column('sell_price', css_class='form-group col-md-6 mb-3'),
                    Column('reorder_threshold', css_class='form-group col-md-6 mb-3'),
                ),
                css_class='border p-3 rounded mb-3'
            )
        )

    def save(self, commit=True):
        instance = super().save(commit=False)
        dynamic_data = {}
        if self.data:
            for key, value in self.data.items():
                if key.startswith('spec_'):
                    clean_key = key.replace('spec_', '')
                    dynamic_data[clean_key] = value
        instance.extra_specs = dynamic_data
        if commit:
            instance.save()
        return instance