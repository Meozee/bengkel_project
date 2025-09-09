# users/models.py

from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'
        MONTIR = 'montir', 'Montir'
        CUSTOMER = 'customer', 'Customer'

    # Nonaktifkan field nama bawaan Django
    first_name = None
    last_name = None

    # Gunakan field baru yang lebih sesuai
    nama_lengkap = models.CharField(max_length=255, help_text="Nama lengkap sesuai KTP.")
    no_wa = models.CharField(max_length=20, unique=True, help_text="Wajib diisi. Format: 628...")
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.STAFF)
    
    # Field ini hanya relevan jika role adalah Montir
    specialty = models.CharField(max_length=100, blank=True, null=True, help_text="Hanya diisi jika role adalah Montir")
    
    def __str__(self):
        return self.username

class Customer(models.Model):
    """Model untuk pelanggan walk-in yang tidak memiliki akun login."""
    nama = models.CharField(max_length=255)
    no_wa = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nama} ({self.no_wa})"