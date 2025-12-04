# apps/expenses/admin.py

from django.contrib import admin
from .models import ExpenseCategory, Expense, RecurringExpense

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(RecurringExpense)
class RecurringExpenseAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'amount', 'due_date_day', 'is_active')
    list_filter = ('is_active', 'category')
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    # Field 'date' SUDAH TIDAK ADA, ganti dengan due_date dan payment_date
    list_display = ('title', 'category', 'amount', 'status', 'due_date', 'payment_date')
    list_filter = ('status', 'due_date', 'payment_date', 'category')
    search_fields = ('title', 'description')
    readonly_fields = ('user',)