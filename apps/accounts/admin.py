# apps/accounts/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import CustomUserCreationForm, CustomUserChangeForm

# --- PERUBAHAN 1: Tambahkan ActivityLog di sini ---
from .models import CustomUser, ActivityLog 

# =========================================================
# BAGIAN BARU: AGAR ACTIVITY LOG MUNCUL DI ADMIN
# =========================================================
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    # Kolom yang akan muncul di tabel list
    list_display = ('timestamp', 'user', 'action_type', 'target_model', 'details')
    # Filter samping untuk memudahkan pencarian
    list_filter = ('action_type', 'target_model')
    # Biar bisa dicari berdasarkan detail atau username
    search_fields = ('details', 'user__username', 'target_model')
    # Biar tidak bisa diedit sembarangan (Log harus murni)
    readonly_fields = ('timestamp',)

# =========================================================
# BAGIAN LAMA (CustomUser): JANGAN DIUBAH, SUDAH BAGUS
# =========================================================
class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    model = CustomUser

    ordering = ('email',)

    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'role',
        'is_staff',
        'is_active',
    )

    list_filter = ('role', 'is_staff', 'is_active')

    fieldsets = (
        (None, {
            'fields': (
                'email',
                'username',
                'password',
            )
        }),
        ('Personal Info', {
            'fields': (
                'first_name',
                'last_name',
                'phone_number',
                'address',
            )
        }),
        ('Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions',
            )
        }),
        ('Important dates', {
            'fields': (
                'last_login',
                'date_joined',
            )
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'email',
                'first_name',
                'last_name',
                'phone_number',
                'address',
                'role',
                'password1',   # FIX
                'password2',   # FIX
            ),
        }),
    )

admin.site.register(CustomUser, CustomUserAdmin)