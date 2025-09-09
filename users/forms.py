# users/forms.py

from django import forms
from .models import Customer, User

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['nama', 'no_wa']
        widgets = {
            'nama': forms.TextInput(attrs={'class': 'form-control'}),
            'no_wa': forms.TextInput(attrs={'class': 'form-control'}),
        }

# =========================================================
# KEMBALI KE VERSI INI UNTUK UserCreationForm
# =========================================================
class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Password")
    password_confirmation = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="Konfirmasi Password")

    class Meta:
        model = User
        fields = ['username', 'nama_lengkap', 'no_wa', 'email', 'role', 'specialty']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'no_wa': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise forms.ValidationError("Password tidak cocok.")
        return password_confirmation

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'nama_lengkap', 'no_wa', 'email', 'role', 'specialty', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'nama_lengkap': forms.TextInput(attrs={'class': 'form-control'}),
            'no_wa': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'specialty': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }