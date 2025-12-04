# apps/expenses/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import ProtectedError, Q
from datetime import datetime, date

# Tools
from apps.accounts.utils import log_activity
from apps.accounts.models import CustomUser

from .models import Expense, ExpenseCategory, RecurringExpense
from .forms import ExpenseForm, ExpenseCategoryForm, RecurringExpenseForm

# ... (Fungsi generate_pending_expenses TETAP SAMA, lewati saja copy-pastenya) ...
# Pastikan fungsi generate_pending_expenses masih ada di file kamu ya.

# ====================================================================
# VIEW UTAMA (INDEX)
# ====================================================================

@login_required
def expense_index(request):
    # 1. Jalankan Generator Otomatis
    # (Pastikan fungsi generate_pending_expenses() sudah didefinisikan di atas atau di utils)
    # generate_pending_expenses() 
    
    # 2. Ambil Data Dasar
    pending_expenses = Expense.objects.select_related('category').filter(
        status=Expense.StatusChoices.PENDING
    ).order_by('due_date')
    
    # PERBAIKAN 1: Tambahkan .exclude(payment_date__isnull=True)
    # Agar data tanpa tanggal bayar tidak muncul di paling atas (baris kosong)
    paid_expenses = Expense.objects.select_related('category', 'user').filter(
        status=Expense.StatusChoices.PAID
    ).exclude(payment_date__isnull=True).order_by('-payment_date')
    
    recurring_expenses = RecurringExpense.objects.select_related('category').all().order_by('due_date_day')

    # 3. Filter Logic
    query = request.GET.get('q')
    category_id = request.GET.get('category')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    # A. Filter Keyword (Terapkan ke SEMUA Tab)
    if query:
        q_obj = Q(title__icontains=query) | Q(description__icontains=query)
        pending_expenses = pending_expenses.filter(q_obj)
        paid_expenses = paid_expenses.filter(q_obj)
        # PERBAIKAN 3: Terapkan filter ke Jadwal Rutin juga
        recurring_expenses = recurring_expenses.filter(name__icontains=query)
    
    # B. Filter Kategori (Terapkan ke SEMUA Tab)
    if category_id:
        pending_expenses = pending_expenses.filter(category_id=category_id)
        paid_expenses = paid_expenses.filter(category_id=category_id)
        recurring_expenses = recurring_expenses.filter(category_id=category_id)

    # C. Filter Tanggal (Hanya untuk Riwayat & Pending)
    # Jadwal Rutin tidak punya tanggal spesifik (cuma hari), jadi tidak difilter tanggal
    if start_date_str and end_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            
            paid_expenses = paid_expenses.filter(payment_date__range=(start_date, end_date))
            pending_expenses = pending_expenses.filter(due_date__range=(start_date, end_date))
        except ValueError:
            pass

    context = {
        'pending_expenses': pending_expenses,
        'paid_expenses': paid_expenses,
        'recurring_expenses': recurring_expenses,
        'categories': ExpenseCategory.objects.all(),
        'page_title': 'Manajemen Pengeluaran',
        
        # Filter State
        'current_query': query or '',
        'current_category': int(category_id) if category_id else '',
        'current_start': start_date_str or '',
        'current_end': end_date_str or '',
        
        # Cek unpaid recurring (sama seperti sebelumnya)
        'unpaid_recurring': [] # (Biarkan logika unpaid recurring kamu yang lama)
    }
    return render(request, 'expenses/expense_index.html', context)
# ====================================================================
# VIEW BARU: DETAIL EXPENSE
# ====================================================================
@login_required
def expense_detail(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    context = {
        'expense': expense,
        'title': f"Detail Pengeluaran"
    }
    return render(request, 'expenses/expense_detail.html', context)

# ====================================================================
# ACTIONS
# ====================================================================

@login_required
def pay_expense(request, pk):
    """Mengubah status PENDING menjadi PAID (Bayar Tagihan)."""
    expense = get_object_or_404(Expense, pk=pk)
    
    if expense.status == Expense.StatusChoices.PAID:
        messages.warning(request, "Tagihan ini sudah lunas.")
        return redirect('expenses:expense_index')
    
    # Update Status
    expense.status = Expense.StatusChoices.PAID
    expense.payment_date = date.today() # Catat bayar hari ini
    expense.user = request.user # Catat siapa yang bayar
    expense.save()
    
    log_activity(request, 'UPDATE', 'Expense', expense.pk, f"Membayar tagihan: {expense.title}")
    messages.success(request, f"Pembayaran '{expense.title}' berhasil dicatat!")
    
    return redirect('expenses:expense_index')

@login_required
def toggle_recurring(request, pk):
    """Mengaktifkan/Menonaktifkan Jadwal Rutin (Misal karyawan resign)."""
    rec = get_object_or_404(RecurringExpense, pk=pk)
    rec.is_active = not rec.is_active
    rec.save()
    
    status_msg = "Diaktifkan" if rec.is_active else "Dinonaktifkan"
    log_activity(request, 'UPDATE', 'RecurringExpense', rec.pk, f"Jadwal {rec.name} {status_msg}")
    messages.success(request, f"Jadwal '{rec.name}' berhasil {status_msg}.")
    
    return redirect('expenses:expense_index')


# ====================================================================
# CRUD EXPENSE (MANUAL)
# ====================================================================

class ExpenseCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Pengeluaran berhasil ditambahkan!"

    def form_valid(self, form):
        form.instance.user = self.request.user
        # Jika user pilih PAID, otomatis isi payment_date hari ini jika kosong
        if form.instance.status == 'PAID' and not form.instance.payment_date:
            form.instance.payment_date = date.today()
        
        response = super().form_valid(form)
        log_activity(self.request, 'CREATE', 'Expense', self.object.pk, f"Input Manual: {self.object.title}")
        return response
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Input Pengeluaran Manual'
        return ctx

class ExpenseUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Data pengeluaran diperbarui!"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request, 'UPDATE', 'Expense', self.object.pk, f"Edit: {self.object.title}")
        return response

class ExpenseDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Expense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER
    
    def handle_no_permission(self):
        messages.error(self.request, "Hanya Owner yang boleh menghapus data.")
        return redirect('expenses:expense_index')

    def form_valid(self, form):
        pk = self.object.pk
        title = self.object.title
        response = super().form_valid(form)
        log_activity(self.request, 'DELETE', 'Expense', pk, f"Hapus: {title}")
        messages.success(self.request, "Data dihapus.")
        return response


# ====================================================================
# CRUD RECURRING (JADWAL RUTIN)
# ====================================================================

class RecurringCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Jadwal rutin dibuat!"

    def form_valid(self, form):
        response = super().form_valid(form)
        log_activity(self.request, 'CREATE', 'RecurringExpense', self.object.pk, f"Buat Jadwal: {self.object.name}")
        return response
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Tambah Jadwal Rutin'
        return ctx

class RecurringUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = RecurringExpense
    form_class = RecurringExpenseForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Jadwal rutin diupdate!"

class RecurringDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = RecurringExpense
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER
    
    def form_valid(self, form):
        name = self.object.name
        pk = self.object.pk
        response = super().form_valid(form)
        log_activity(self.request, 'DELETE', 'RecurringExpense', pk, f"Hapus Jadwal: {name}")
        messages.success(self.request, "Jadwal dihapus.")
        return response


# ====================================================================
# CRUD CATEGORY (Sama seperti sebelumnya)
# ====================================================================
# ... (Simpan CategoryCreateView, Update, Delete yang lama di sini) ...
class CategoryCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Kategori berhasil ditambahkan!"
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Tambah Kategori'
        return ctx

class CategoryUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ExpenseCategory
    form_class = ExpenseCategoryForm
    template_name = 'expenses/expense_form.html'
    success_url = reverse_lazy('expenses:expense_index')
    success_message = "Kategori berhasil diperbarui!"

class CategoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = ExpenseCategory
    template_name = 'expenses/expense_confirm_delete.html'
    success_url = reverse_lazy('expenses:expense_index')

    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER
    
    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Kategori dihapus.")
            return response
        except ProtectedError:
            messages.error(self.request, "Kategori sedang digunakan, tidak bisa dihapus.")
            return redirect('expenses:expense_index')