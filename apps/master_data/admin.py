# apps/master_data/admin.py

from django.contrib import admin
from .models import Mechanic, Customer, Vehicle, Service, Vendor # 1. Impor Vendor

@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'specialty')
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'email')
    search_fields = ('name', 'phone_number')

@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('license_plate', 'customer', 'brand', 'model')
    search_fields = ('license_plate', 'customer__name')
    list_filter = ('brand', 'model')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    search_fields = ('name',)

# 2. Tambahkan registrasi untuk Vendor
@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'phone_number')
    search_fields = ('name', 'contact_person')