# apps/expenses/admin.py
from django.contrib import admin
from .models import ExpenseCategory, Expense

admin.site.register(ExpenseCategory)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('date', 'category', 'amount', 'description', 'user')
    list_filter = ('date', 'category', 'user')
    search_fields = ('description',)