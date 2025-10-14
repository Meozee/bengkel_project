# apps/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager  # <-- Sudah benar

class CustomUser(AbstractUser):
    username = None  # Menghapus username
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []  # Tidak perlu username

    # 👇 INI YANG KAMU LUPA!
    objects = CustomUserManager()

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'Admin'
        STAFF = 'STAFF', 'Staff'

    role = models.CharField(
        _("Role"),
        max_length=50,
        choices=Role.choices,
        default=Role.STAFF
    )

    def __str__(self):
        return self.email