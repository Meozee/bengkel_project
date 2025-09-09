# transactions/forms.py

from django import forms
from .models import Transaksi
from users.models import Customer, User # <-- PERBAIKAN: Ganti Montir dengan User

class TransaksiForm(forms.ModelForm):
    # PERBAIKAN: Definisikan field 'montir' untuk merujuk ke User
    montir = forms.ModelChoiceField(
        queryset=User.objects.filter(role='montir'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Transaksi
        # Pastikan 'montir' ada di fields
        fields = ['customer', 'montir', 'jenis_service', 'biaya_jasa']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'jenis_service': forms.Select(attrs={'class': 'form-control'}),
            'biaya_jasa': forms.NumberInput(attrs={'class': 'form-control'}),
        }