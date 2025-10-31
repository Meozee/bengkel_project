# apps/expenses/views.py

from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import ProtectedError

from .models import Expense, ExpenseCategory
from .forms import ExpenseForm, ExpenseCategoryForm

# ====================================================================
# View Utama (Tabbed List)
# ====================================================================

@login_required
def expense_index(request):
    """
    Menampilkan halaman utama Pengeluaran dengan dua tab:
    1. Daftar semua Expense (Pengeluaran)
    2. Daftar semua ExpenseCategory (Kategori)
    """
    expenses = Expense.objects.select_related('category', 'user').all()
    categories = ExpenseCategory.objects.all()
    
    context = {
        'expenses': expenses,
        'categories': categories,
        'page_title': 'Data Pengeluaran'
    }
    return render(request, 'expenses/expense_index.html', context)


# ====================================================================
# CRUD Views untuk Expense (Pengeluaran)
# ====================================================================

class ExpenseCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html' # Template form generik
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Data pengeluaran baru berhasil ditambahkan!"

    def form_valid(self, form):
        # Set 'user' yang mencatat secara otomatis
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        # Menambahkan judul halaman ke context
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Pengeluaran'
        context['card_title'] = 'Edit Data Pengeluaran'
        return context

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html' # Template konfirmasi hapus
    success_url = reverse_lazy('expenses:expense_index')

    def delete(self, request, *args, **kwargs):
        # Menambahkan pesan sukses secara manual karena DeleteView tidak punya SuccessMessageMixin
        messages.success(self.request, "Data pengeluaran telah berhasil dihapus.")
        return super().delete(request, *args, **kwargs)

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
    template_name = 'expenses/expense_form.html' # Pakai template form yang sama
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Kategori pengeluaran baru berhasil ditambahkan!"

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Edit Kategori'
        context['card_title'] = 'Edit Data Kategori'
        return context

class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = ExpenseCategory
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def delete(self, request, *args, **kwargs):
        try:
            # Coba hapus dulu
            response = super().delete(request, *args, **kwargs)
            messages.success(self.request, "Kategori telah berhasil dihapus.")
            return response
        except ProtectedError:
            # Tangkap error jika kategori masih dipakai (karena on_delete=PROTECT)
            messages.error(self.request, "Kategori ini tidak bisa dihapus karena masih digunakan oleh data pengeluaran lain.")
            # Kembalikan ke halaman konfirmasi hapus
            return self.get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Hapus Kategori'
        return context