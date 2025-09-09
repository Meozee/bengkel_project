# users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Customer

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Informasi Tambahan', {'fields': ('nama_lengkap', 'no_wa', 'role', 'specialty')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informasi Tambahan', {'fields': ('nama_lengkap', 'no_wa', 'role', 'specialty')}),
    )
    list_display = ('username', 'nama_lengkap', 'no_wa', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'nama_lengkap', 'no_wa')

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('nama', 'no_wa', 'created_at')
    search_fields = ('nama', 'no_wa')
    ordering = ('-created_at',)