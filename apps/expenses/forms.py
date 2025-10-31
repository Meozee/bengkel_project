# apps/expenses/forms.py

from django import forms
from .models import Expense, ExpenseCategory

class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        # 'user' akan di-set di view, jadi tidak perlu ada di form
        fields = ['date', 'category', 'amount', 'description']
        
        # Tambahkan widget untuk tampilan yang lebih baik
        widgets = {
            'date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            ),
            'category': forms.Select(
                attrs={'class': 'form-select'}
            ),
            'amount': forms.NumberInput(
                attrs={'class': 'form-control'}
            ),
            'description': forms.Textarea(
                attrs={'rows': 3, 'class': 'form-control'}
            ),
        }

class ExpenseCategoryForm(forms.ModelForm):
    class Meta:
        model = ExpenseCategory
        fields = ['name']
        widgets = {
            'name': forms.TextInput(
                attrs={'class': 'form-control', 'placeholder': 'Contoh: Gaji Karyawan'}
            )
        }