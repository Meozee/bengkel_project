# apps/transactions/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Transaction, TransactionItem, TransactionService
from apps.inventory.models import InventoryItem, InventoryLog

# --- Helper Function untuk Log Inventory ---
def _create_inventory_log(item, change, before, after, source_type, source_id, note):
    InventoryLog.objects.create(
        item=item,
        change=change,
        before=before,
        after=after,
        source_type=source_type,
        source_id=source_id,
        note=note
    )

# 1. Simpan Status Lama (untuk deteksi perubahan)
@receiver(pre_save, sender=Transaction)
def store_old_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Transaction.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

# 2. Logic Perubahan Status Transaksi
@receiver(post_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, created, **kwargs):
    if created: return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # Jika berubah jadi COMPLETED -> Potong Stok & Set Waktu
    if old_status != Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.COMPLETED:
        with transaction.atomic():
            # Set Waktu Selesai jika belum ada
            if not instance.completed_at:
                Transaction.objects.filter(pk=instance.pk).update(completed_at=timezone.now())

            # Potong Stok
            for detail in instance.items.all():
                item = InventoryItem.objects.select_for_update().get(pk=detail.item.pk)
                if item.quantity < detail.quantity:
                    raise ValidationError(f"Stok {item.name} tidak cukup untuk menyelesaikan transaksi ini.")
                
                before = item.quantity
                item.quantity -= detail.quantity
                item.save()
                
                _create_inventory_log(item, -detail.quantity, before, item.quantity, 
                                    "TRANSACTION_COMPLETED", instance.pk, f"Invoice {instance.invoice_number}")

    # Jika berubah jadi CANCELLED (dari Completed) -> Balikin Stok
    elif old_status == Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.CANCELLED:
        with transaction.atomic():
            for detail in instance.items.all():
                item = InventoryItem.objects.select_for_update().get(pk=detail.item.pk)
                before = item.quantity
                item.quantity += detail.quantity
                item.save()
                
                _create_inventory_log(item, detail.quantity, before, item.quantity, 
                                    "TRANSACTION_CANCELLED", instance.pk, f"Batal Invoice {instance.invoice_number}")

# 3. Hitung Ulang Total Harga (Setiap kali Item/Service ditambah/hapus)
@receiver([post_save, post_delete], sender=TransactionItem)
@receiver([post_save, post_delete], sender=TransactionService)
def update_transaction_total(sender, instance, **kwargs):
    txn = instance.transaction
    items_total = sum(item.subtotal for item in txn.items.all())
    services_total = sum(svc.subtotal for svc in txn.services.all())
    
    grand_total = items_total + services_total + txn.other_charges - txn.discount_amount
    Transaction.objects.filter(pk=txn.pk).update(total_amount=grand_total)