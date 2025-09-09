# core/models.py

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

class ActivityLog(models.Model):
    class ActionTypes(models.TextChoices):
        CREATE = 'CREATE', 'Pembuatan'
        UPDATE = 'UPDATE', 'Pembaruan'
        DELETE = 'DELETE', 'Penghapusan'
        LOGIN = 'LOGIN', 'Login'
        LOGOUT = 'LOGOUT', 'Logout'
        TRANSACTION_COMPLETE = 'TRX_COMPLETE', 'Transaksi Selesai'

    # SIAPA yang melakukan aksi
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        help_text="Pengguna yang melakukan aksi."
    )
    # APA aksinya
    action_type = models.CharField(
        max_length=20, 
        choices=ActionTypes.choices,
        help_text="Jenis aksi yang dilakukan."
    )
    # DETAIL aksinya (dalam bentuk teks)
    action_details = models.TextField(
        help_text="Deskripsi detail dari aksi yang dilakukan."
    )
    # KAPAN aksi dilakukan
    timestamp = models.DateTimeField(
        auto_now_add=True
    )
    # STATUS notifikasi (untuk titik merah)
    is_read = models.BooleanField(
        default=False
    )

    # Generic Foreign Key: untuk menautkan ke OBJEK APAPUN (User, Customer, Transaksi, dll.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.actor.username} - {self.get_action_type_display()} - {self.timestamp.strftime('%d %b %Y, %H:%M')}"

    class Meta:
        ordering = ['-timestamp']
        verbose_name_plural = "Activity Logs"