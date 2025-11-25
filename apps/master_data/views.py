# apps/master_data/views.py

from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages

# Import Helper Logging yang sudah kita buat
from apps.accounts.utils import log_activity
from apps.accounts.models import CustomUser

from .models import Mechanic, Customer, Vehicle, Service, Vendor
from .forms import MechanicForm, CustomerForm, VehicleForm, ServiceForm, VendorForm

# Halaman utama untuk Data Master
def master_data_index(request):
    context = {
        'page_title': 'Data Master'
    }
    return render(request, 'master_data/master_data_index.html', context)

# =================================================================
# BASE VIEWS (LOGGING & SECURITY INJECTED HERE)
# =================================================================

class BaseListView(LoginRequiredMixin, ListView):
    """Base ListView dengan fitur Login Required & Pagination"""
    paginate_by = 10
    login_url = 'login'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            # Menggunakan icontains pada field 'name' (default)
            # Untuk model yang tidak punya 'name' (misal Vehicle), 
            # ini akan di-override di class anaknya.
            if hasattr(self.model, 'name'):
                queryset = queryset.filter(name__icontains=query)
        return queryset

class BaseCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Base CreateView dengan Logging Otomatis"""
    template_name = 'master_data/master_data_form.html'
    login_url = 'login'
    
    def get_success_message(self, cleaned_data):
        return f"{self.model._meta.verbose_name.title()} berhasil dibuat."

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # --- LOGGING CREATE ---
        log_activity(
            self.request,
            action_type='CREATE',
            target_model=self.model.__name__,
            target_id=self.object.pk,
            details=f"Menambahkan data {self.model._meta.verbose_name}: {self.object}"
        )
        return response

class BaseUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """Base UpdateView dengan Logging Otomatis"""
    template_name = 'master_data/master_data_form.html'
    login_url = 'login'
    
    def get_success_message(self, cleaned_data):
        return f"{self.model._meta.verbose_name.title()} berhasil diperbarui."

    def form_valid(self, form):
        # Ambil data sebelum diubah (opsional, jika ingin log detail perubahan)
        # Disini kita log simple saja
        response = super().form_valid(form)
        
        # --- LOGGING UPDATE ---
        log_activity(
            self.request,
            action_type='UPDATE',
            target_model=self.model.__name__,
            target_id=self.object.pk,
            details=f"Mengubah data {self.model._meta.verbose_name}: {self.object}"
        )
        return response

class BaseDeleteView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, DeleteView):
    """
    Base DeleteView dengan:
    1. Logging Otomatis
    2. Proteksi (HANYA OWNER YANG BISA HAPUS)
    """
    template_name = 'master_data/master_data_confirm_delete.html'
    login_url = 'login'
    
    # Logic: Admin Biasa dilarang hapus
    def test_func(self):
        return self.request.user.role == CustomUser.RoleChoices.OWNER

    def handle_no_permission(self):
        messages.error(self.request, "Akses Ditolak! Hanya Owner yang dapat menghapus data.")
        return redirect('master_data:master_data_index')

    def get_success_message(self, cleaned_data):
        return "Data berhasil dihapus."

    def form_valid(self, form):
        # Simpan nama object sebelum dihapus untuk log
        object_name = str(self.object)
        object_pk = self.object.pk
        model_name = self.model.__name__

        response = super().form_valid(form)

        # --- LOGGING DELETE ---
        log_activity(
            self.request,
            action_type='DELETE',
            target_model=model_name,
            target_id=object_pk,
            details=f"Menghapus permanent data {self.model._meta.verbose_name}: {object_name}"
        )
        return response

# =================================================================
# CONCRETE VIEWS (TIDAK PERLU DIUBAH BANYAK)
# =================================================================

# === Customer Views ===
class CustomerListView(BaseListView):
    model = Customer
    template_name = 'master_data/customer_list.html'

class CustomerCreateView(BaseCreateView):
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy('master_data:customer_list')

class CustomerUpdateView(BaseUpdateView):
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy('master_data:customer_list')

class CustomerDeleteView(BaseDeleteView):
    model = Customer
    success_url = reverse_lazy('master_data:customer_list')


# === Mechanic Views ===
class MechanicListView(BaseListView):
    model = Mechanic
    template_name = 'master_data/mechanic_list.html'

class MechanicCreateView(BaseCreateView):
    model = Mechanic
    form_class = MechanicForm
    success_url = reverse_lazy('master_data:mechanic_list')

class MechanicUpdateView(BaseUpdateView):
    model = Mechanic
    form_class = MechanicForm
    success_url = reverse_lazy('master_data:mechanic_list')

class MechanicDeleteView(BaseDeleteView):
    model = Mechanic
    success_url = reverse_lazy('master_data:mechanic_list')


# === Vehicle Views ===
class VehicleListView(BaseListView): 
    # Note: Kita ganti jadi BaseListView biar kena LoginRequired juga
    model = Vehicle
    template_name = 'master_data/vehicle_list.html'
    
    def get_queryset(self):
        # Override khusus karena vehicle cari berdasarkan plat no
        queryset = super(ListView, self).get_queryset().select_related('customer')
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(license_plate__icontains=query)
        return queryset
        
class VehicleCreateView(BaseCreateView):
    model = Vehicle
    form_class = VehicleForm
    success_url = reverse_lazy('master_data:vehicle_list')

class VehicleUpdateView(BaseUpdateView):
    model = Vehicle
    form_class = VehicleForm
    success_url = reverse_lazy('master_data:vehicle_list')

class VehicleDeleteView(BaseDeleteView):
    model = Vehicle
    success_url = reverse_lazy('master_data:vehicle_list')


# === Service Views ===
class ServiceListView(BaseListView):
    model = Service
    template_name = 'master_data/service_list.html'

class ServiceCreateView(BaseCreateView):
    model = Service
    form_class = ServiceForm
    success_url = reverse_lazy('master_data:service_list')

class ServiceUpdateView(BaseUpdateView):
    model = Service
    form_class = ServiceForm
    success_url = reverse_lazy('master_data:service_list')

class ServiceDeleteView(BaseDeleteView):
    model = Service
    success_url = reverse_lazy('master_data:service_list')


# === Vendor Views ===
class VendorListView(BaseListView):
    model = Vendor
    template_name = 'master_data/vendor_list.html'

class VendorCreateView(BaseCreateView):
    model = Vendor
    form_class = VendorForm
    success_url = reverse_lazy('master_data:vendor_list')

class VendorUpdateView(BaseUpdateView):
    model = Vendor
    form_class = VendorForm
    success_url = reverse_lazy('master_data:vendor_list')

class VendorDeleteView(BaseDeleteView):
    model = Vendor
    success_url = reverse_lazy('master_data:vendor_list')