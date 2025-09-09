# core/signals.py

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.contrib.auth.signals import user_logged_in, user_logged_out

from .models import ActivityLog
from users.models import Customer
# PERBAIKAN: Impor semua model dari inventory di sini
from inventory.models import Produk, Merek, Kategori, Supplier, TipePembelian

User = get_user_model()
_user = None

def set_current_user(user):
    global _user
    _user = user

# --- Sinyal untuk CRUD ---
@receiver(post_save, sender=User)
@receiver(post_save, sender=Customer)
@receiver(post_save, sender=Produk)
@receiver(post_save, sender=Merek)
@receiver(post_save, sender=Kategori)
@receiver(post_save, sender=Supplier)
@receiver(post_save, sender=TipePembelian)
def log_save_activity(sender, instance, created, **kwargs):
    actor = _user
    if not actor: return

    action_type = ActivityLog.ActionTypes.CREATE if created else ActivityLog.ActionTypes.UPDATE
    model_name = sender._meta.verbose_name.title()
    ActivityLog.objects.create(
        actor=actor,
        action_type=action_type,
        action_details=f"Melakukan '{action_type}' pada {model_name}: '{str(instance)}'",
        content_object=instance
    )

@receiver(post_delete, sender=User)
@receiver(post_delete, sender=Customer)
@receiver(post_delete, sender=Produk)
@receiver(post_delete, sender=Merek)
@receiver(post_delete, sender=Kategori)
@receiver(post_delete, sender=Supplier)
@receiver(post_delete, sender=TipePembelian)
def log_delete_activity(sender, instance, **kwargs):
    actor = _user
    if not actor: return

    model_name = sender._meta.verbose_name.title()
    ActivityLog.objects.create(
        actor=actor,
        action_type=ActivityLog.ActionTypes.DELETE,
        action_details=f"Menghapus {model_name}: '{str(instance)}'",
        content_object=instance
    )

# --- Sinyal untuk Login & Logout ---
@receiver(user_logged_in)
def log_login_activity(sender, request, user, **kwargs):
    ActivityLog.objects.create(
        actor=user,
        action_type=ActivityLog.ActionTypes.LOGIN,
        action_details=f"User '{user.username}' berhasil login.",
        content_object=user
    )

@receiver(user_logged_out)
def log_logout_activity(sender, request, user, **kwargs):
    if not user: return
    ActivityLog.objects.create(
        actor=user,
        action_type=ActivityLog.ActionTypes.LOGOUT,
        action_details=f"User '{user.username}' berhasil logout.",
        content_object=user
    )