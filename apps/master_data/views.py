from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from .models import Mechanic, Customer, Vehicle, Service, Vendor
from .forms import MechanicForm, CustomerForm, VehicleForm, ServiceForm, VendorForm

# Halaman utama untuk Data Master
def master_data_index(request):
    context = {
        'page_title': 'Data Master'
    }
    return render(request, 'master_data/master_data_index.html', context)

# Generic Views untuk CRUD (lebih efisien)
class BaseListView(ListView):
    paginate_by = 10
    
    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get('q')
        if query:
            # Pastikan model punya 'name' atau sesuaikan field pencarian
            queryset = queryset.filter(name__icontains=query)
        return queryset

class BaseCreateView(SuccessMessageMixin, CreateView):
    template_name = 'master_data/master_data_form.html'
    
    def get_success_message(self, cleaned_data):
        return f"{self.model._meta.verbose_name.title()} berhasil dibuat."

class BaseUpdateView(SuccessMessageMixin, UpdateView):
    template_name = 'master_data/master_data_form.html'
    
    def get_success_message(self, cleaned_data):
        return f"{self.model._meta.verbose_name.title()} berhasil diperbarui."

class BaseDeleteView(SuccessMessageMixin, DeleteView):
    template_name = 'master_data/master_data_confirm_delete.html'
    
    def get_success_message(self, cleaned_data):
        return f"{self.object} berhasil dihapus."


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

# === Lanjutkan pola yang sama untuk Vehicle, Service, dan Vendor... ===
# (Ini adalah contoh lengkap, cukup salin semua)

# === Vehicle Views ===
class VehicleListView(ListView): # Vehicle pakai ListView biasa karena pencarian lebih kompleks
    model = Vehicle
    template_name = 'master_data/vehicle_list.html'
    paginate_by = 10
    def get_queryset(self):
        queryset = super().get_queryset().select_related('customer')
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