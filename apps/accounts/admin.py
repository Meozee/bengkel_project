from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from django.contrib.auth.forms import UserCreationForm, UserChangeForm # 1. Impor form

class CustomUserAdmin(UserAdmin):
    """
    Konfigurasi tampilan untuk CustomUser di halaman Admin.
    """
    # 2. Tentukan form yang akan digunakan
    add_form = UserCreationForm
    form = UserChangeForm
    
    model = CustomUser
    ordering = ('email',)

    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_display_links = ('email',)
    list_filter = ('role', 'is_staff', 'is_active', 'groups')
    search_fields = ('email', 'first_name', 'last_name')

    # fieldsets untuk halaman edit user yang sudah ada
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('User Role', {'fields': ('role',)}),
    )
    
    # add_fieldsets untuk halaman pembuatan user baru
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'password2', 'role'),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)