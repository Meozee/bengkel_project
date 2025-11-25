from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from .forms import CustomUserCreationForm, CustomUserChangeForm 

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser
    
    ordering = ('email',)
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_staff', 'is_active') # Tambah username biar keliatan di list
    list_filter = ('role', 'is_staff', 'is_active')
    
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}), # Tambah username
        ('Personal Info', {'fields': ('first_name', 'last_name', 'phone_number', 'address')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser', 'groups')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # TAMBAHKAN 'username' DI SINI JUGA
            'fields': ('username', 'email', 'first_name', 'last_name', 'role', 'password', 'password2'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)