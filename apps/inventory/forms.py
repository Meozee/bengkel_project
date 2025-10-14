from django import forms
from .models import InventoryItem, Category

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class InventoryForm(forms.ModelForm):
    class Meta:
        model = InventoryItem
        fields = [
            'name', 'category', 'sku', 'description', 
            'sell_price', 'reorder_threshold', 'item_type',
            'quantity', 'buy_price' # Tetap dimasukkan agar nilainya tampil
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sell_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'reorder_threshold': forms.NumberInput(attrs={'class': 'form-control'}),
            'item_type': forms.Select(attrs={'class': 'form-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'buy_price': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Jika form ini sedang mengedit instance yang sudah ada
        if self.instance and self.instance.pk:
            # Buat field 'quantity' dan 'buy_price' menjadi disabled (read-only)
            self.fields['quantity'].disabled = True
            self.fields['quantity'].help_text = "Jumlah stok diatur melalui modul Pembelian/Transaksi."
            
            self.fields['buy_price'].disabled = True
            self.fields['buy_price'].help_text = "Harga beli diatur melalui modul Pembelian."