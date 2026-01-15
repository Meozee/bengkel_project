from django import forms
from django.core.exceptions import ValidationError
from .models import InventoryItem, Category

class CategoryForm(forms.ModelForm):
    # Radio Button untuk Status Kategori
    STATUS_CHOICES = [
        (True, 'Aktif (Digunakan)'),
        (False, 'Non-Aktif (Arsipkan)'),
    ]
    is_active = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        widget=forms.RadioSelect, 
        initial=True,
        label="Status Kategori"
    )

    class Meta:
        model = Category
        fields = ['name', 'description', 'required_specs', 'is_active']

    def clean(self):
        cleaned_data = super().clean()
        is_active = cleaned_data.get('is_active') == 'True'
        
        # Validasi: Jangan non-aktifkan kategori jika masih ada item AKTIF di dalamnya
        if not is_active and self.instance.pk:
            if self.instance.inventoryitem_set.filter(is_active=True).exists():
                raise ValidationError({
                    'is_active': "Kategori ini tidak bisa dinonaktifkan karena masih memiliki Item yang Aktif. Nonaktifkan itemnya terlebih dahulu."
                })
        
        cleaned_data['is_active'] = is_active
        return cleaned_data


class InventoryForm(forms.ModelForm):
    # Radio Button untuk Status Item
    STATUS_CHOICES = [
        (True, 'Aktif (Muncul di Sistem)'),
        (False, 'Non-Aktif (Diarsipkan/Discontinue)'),
    ]
    is_active = forms.ChoiceField(
        choices=STATUS_CHOICES, 
        widget=forms.RadioSelect, 
        initial=True,
        label="Status Ketersediaan"
    )

    class Meta:
        model = InventoryItem
        fields = [
            'category', 'name', 'sku', 'item_type', 
            'buy_price', 'sell_price', 'reorder_threshold', 
            'description', 'is_active', 'quantity' 
            # Note: quantity dimunculkan jika ingin edit manual, 
            # tapi validasi tetap berjalan.
        ]

    def clean(self):
        cleaned_data = super().clean()
        # Konversi string 'True'/'False' dari radio button kembali ke Boolean
        is_active_input = cleaned_data.get('is_active')
        is_active_bool = is_active_input == 'True'
        
        # Ambil quantity (bisa dari input user atau instance database)
        quantity = cleaned_data.get('quantity')
        if quantity is None and self.instance.pk:
            quantity = self.instance.quantity
            
        # === LOGIKA SATPAM (GUARD) ===
        # Jika user memilih NON-AKTIF (False), tapi Stok > 0
        if is_active_bool is False and quantity > 0:
            # Raise Error spesifik pada field is_active
            raise ValidationError({
                'is_active': f"DILARANG: Item masih memiliki sisa stok {quantity}. Habiskan stok (transaksi/write-off) sebelum menonaktifkan item ini."
            })

        # Set value boolean yang benar ke cleaned_data
        cleaned_data['is_active'] = is_active_bool
        return cleaned_data