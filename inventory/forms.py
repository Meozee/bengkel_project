# inventory/forms.py
from django import forms
from .models import Produk

class ProdukForm(forms.ModelForm):
    class Meta:
        model = Produk
        fields = [
            'nama_produk', 'merek', 'kategori', 'tipe', 
            'harga_jual_standar', 'ambang_batas_stok'
        ]
        widgets = {
            'nama_produk': forms.TextInput(attrs={'class': 'form-control'}),
            'merek': forms.Select(attrs={'class': 'form-select'}),
            'kategori': forms.Select(attrs={'class': 'form-select'}),
            'tipe': forms.Select(attrs={'class': 'form-select'}),
            'harga_jual_standar': forms.NumberInput(attrs={'class': 'form-control'}),
            'ambang_batas_stok': forms.NumberInput(attrs={'class': 'form-control'}),
        }