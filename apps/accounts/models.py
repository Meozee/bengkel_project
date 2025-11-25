# apps/accounts/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

class CustomUser(AbstractUser):
    class RoleChoices(models.TextChoices):
        OWNER = 'OWNER', 'Owner (Full Access)'
        ADMIN = 'ADMIN', 'Admin (Restricted)'

    role = models.CharField(
        max_length=20, 
        choices=RoleChoices.choices, 
        default=RoleChoices.ADMIN,
        help_text="Owner bisa segalanya, Admin tidak bisa hapus data & lihat log."
    )
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def is_owner(self):
        return self.role == self.RoleChoices.OWNER

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ActivityLog(models.Model):
    """
    Mencatat semua aktivitas user: Login, Create, Update, Delete, Print, dll.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=50) # CONTOH: 'LOGIN', 'LOGOUT', 'CREATE_TRANSACTION', 'DELETE_ITEM'
    target_model = models.CharField(max_length=100, blank=True) # CONTOH: 'Transaction', 'InventoryItem'
    target_id = models.CharField(max_length=100, blank=True) # ID object yang diubah
    details = models.TextField(blank=True) # Detail perubahan (misal: Status Pending -> Paid)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp}] {self.user} - {self.action_type}"