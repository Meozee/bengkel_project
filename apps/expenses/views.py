# apps/expenses/views.py

from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import ProtectedError, Q
from datetime import datetime

# Import Helper Logging & User Role
from apps.accounts.utils import log_activity
from apps.accounts.models import CustomUser

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm

# ====================================================================
# View Utama (Tabbed List)
# ====================================================================

@login_required
def expense_index(request):
    # 1. Base Query
    expenses = Expense.objects.select_related('category', 'user').order_by('-date')
    
    # 2. Filter Logic
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # A. Filter Keyword (Deskripsi / User)
    if query:
        expenses = expenses.filter(
            Q(description__icontains=query) | 
            Q(user__username__icontains=query)
        )
    
    # B. Filter Kategori
    if category_id:
        expenses = expenses.filter(category_id=category_id)

    # C. Filter Tanggal
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Expenses menggunakan DateField, jadi filter range tanggal (inclusive) cukup aman
            expenses = expenses.filter(date__range=(start_date, end_date))
        except ValueError:
            pass

    categories = ExpenseCategory.objects.all()
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'page_title': 'Data Pengeluaran',
        
        # Maintain State
        'current_query': query or '',
        'current_category': int(category_id) if category_id else '',
        'current_start': start_date_str or '',
        'current_end': end_date_str or '',
    }
    return render(request, 'expenses/expense_index.html', context)


# ====================================================================
# CRUD Views untuk Expense (Pengeluaran)
# ====================================================================

class ExpenseCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Data pengeluaran baru berhasil ditambahkan!"

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        
        log_activity(
            self.request, 'CREATE', 'Expense', self.object.pk,
            f"Input pengeluaran: {self.object.amount} ({self.object.category})"
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tambah Pengeluaran'
        context['card_title'] = 'Formulir Pengeluaran Baru'
        return context

class ExpenseUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Data pengeluaran berhasil diperbarui!"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(
            self.request, 'UPDATE', 'Expense', self.object.pk,
            f"Edit pengeluaran: {self.object.amount} ({self.object.category})"
        )
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Pengeluaran'
        context['card_title'] = 'Edit Data Pengeluaran'
        return context

class ExpenseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER

    def handle_no_permission(self):
        messages.error(self.request, "Akses Ditolak! Hanya Owner yang boleh menghapus data keuangan.")
        return redirect('expenses:expense_index')

    def form_valid(self, form):
        amount = self.object.amount
        desc = self.object.description
        pk = self.object.pk
        
        response = super().form_valid(form)
        
        log_activity(
            self.request, 'DELETE', 'Expense', pk,
            f"Menghapus pengeluaran: {amount} - {desc}"
        )
        messages.success(self.request, "Data pengeluaran telah berhasil dihapus.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Pengeluaran'
        return context


# ====================================================================
# CRUD Views untuk ExpenseCategory (Kategori)
# ====================================================================

class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Kategori pengeluaran baru berhasil ditambahkan!"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request, 'CREATE', 'ExpenseCategory', self.object.pk, f"Tambah Kategori: {self.object.name}")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Tambah Kategori'
        context['card_title'] = 'Formulir Kategori Baru'
        return context

class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Kategori pengeluaran berhasil diperbarui!"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request, 'UPDATE', 'ExpenseCategory', self.object.pk, f"Edit Kategori: {self.object.name}")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Kategori'
        context['card_title'] = 'Edit Data Kategori'
        return context

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ExpenseCategory
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER
    
    def handle_no_permission(self):
        messages.error(self.request, "Akses Ditolak! Hanya Owner yang boleh menghapus kategori.")
        return redirect('expenses:expense_index')

    def form_valid(self, form):
        try:
            name = self.object.name
            pk = self.object.pk
            response = super().form_valid(form)
            
            log_activity(self.request, 'DELETE', 'ExpenseCategory', pk, f"Hapus Kategori: {name}")
            messages.success(self.request, "Kategori telah berhasil dihapus.")
            return response
        except ProtectedError:
            messages.error(self.request, "Kategori ini tidak bisa dihapus karena masih digunakan oleh data pengeluaran lain.")
            return redirect('expenses:expense_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Kategori'
        return context