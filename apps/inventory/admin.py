from django import forms
from django.contrib import admin
from django.db.models import F
from .models import Category, InventoryItem

class InventoryItemAdminForm(forms.ModelForm):
    # Field virtual untuk Admin
    volume = forms.CharField(required=False, label="Volume (Oli)")
    sae = forms.CharField(required=False, label="SAE (Oli)")
    position = forms.CharField(required=False, label="Posisi (Kampas)")

    class Meta:
        model = InventoryItem
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ambil data dari JSON ke field virtual saat loading
        if self.instance and self.instance.extra_specs:
            specs = self.instance.extra_specs
            self.initial['volume'] = specs.get('volume', '')
            self.initial['sae'] = specs.get('sae', '')
            self.initial['position'] = specs.get('position', '')

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Bungkus kembali ke JSON sebelum simpan
        instance.extra_specs = {
            'volume': self.cleaned_data.get('volume'),
            'sae': self.cleaned_data.get('sae'),
            'position': self.cleaned_data.get('position'),
        }
        if commit:
            instance.save()
        return instance

@admin.register(InventoryItem)
class InventoryItemAdmin(admin.ModelAdmin):
    form = InventoryItemAdminForm # Pakai form kustom
    list_display = ('name', 'category', 'sku', 'sell_price', 'quantity', 'is_low_stock')
    search_fields = ('name', 'sku')
    list_filter = ('category',)
    readonly_fields = ('quantity', 'buy_price')
    exclude = ('extra_specs',) # Sembunyikan kotak JSON asli