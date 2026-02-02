# apps/purchases/forms.py

from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderItem

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = [
            'vendor', 'order_date', 'status', 
            'purchaser_mechanic', 'purchaser_custom', 
            'expected_delivery_date', 'notes'
        ]
        widgets = {
            'vendor': forms.Select(attrs={'class': 'form-select select2-enable'}),
            'order_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            # Buat status jadi 'hidden' atau 'disabled' agar tidak bisa diubah user
            'status': forms.Select(attrs={
                'class': 'form-select bg-light', 
                'style': 'pointer-events: none;', # User tidak bisa klik
                'tabindex': '-1' # Tidak bisa di-tab
            }),
            'purchaser_mechanic': forms.Select(attrs={'class': 'form-select'}),
            'purchaser_custom': forms.TextInput(attrs={'class': 'form-control'}),
            'expected_delivery_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['status'].initial = 'PENDING'
        
        # Opsi Alternatif yang Lebih Aman (Backend side):
        # Jika Anda ingin memastikan user tidak meng-hack HTML untuk ganti status:
        # Biarkan field disabled di UI, tapi inject data di method clean().
    
    def clean_status(self):
        # Pastikan jika form disubmit, status tetap menggunakan instance yang ada
        # atau default 'PENDING' jika baru.
        if self.instance.pk:
            return self.instance.status
        return self.cleaned_data.get('status', 'PENDING')

class PurchaseOrderItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrderItem
        fields = ['item', 'quantity', 'unit_price']
        widgets = {
            'item': forms.Select(attrs={'class': 'form-select item-select'}), 
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'unit_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

PurchaseOrderItemFormSet = inlineformset_factory(
    PurchaseOrder,
    PurchaseOrderItem,
    form=PurchaseOrderItemForm,
    extra=1, 
    can_delete=True,
    can_delete_extra=True
)