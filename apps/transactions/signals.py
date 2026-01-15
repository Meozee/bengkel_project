# apps/transactions/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
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


# ========== TRANSACTION STATUS HANDLING ==========

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
    if created: 
        return

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


# ========== TRANSACTION ITEM HANDLING (YANG BARU) ==========

# 3. Simpan data lama TransactionItem sebelum update/delete
@receiver(pre_save, sender=TransactionItem)
def store_old_transaction_item(sender, instance, **kwargs):
    """Simpan data item lama untuk detect perubahan"""
    if instance.pk:
        try:
            old = TransactionItem.objects.get(pk=instance.pk)
            instance._old_item_id = old.item.pk
            instance._old_quantity = old.quantity
        except TransactionItem.DoesNotExist:
            instance._old_item_id = None
            instance._old_quantity = None
    else:
        instance._old_item_id = None
        instance._old_quantity = None


@receiver(post_save, sender=TransactionItem)
def handle_transaction_item_change(sender, instance, created, **kwargs):
    """Handle perubahan item dalam transaksi yang sudah COMPLETED"""
    
    # Hanya proses jika transaksi sudah COMPLETED
    if instance.transaction.status != Transaction.StatusChoices.COMPLETED:
        return
    
    # Jika baru ditambahkan ke transaksi yang sudah COMPLETED
    if created:
        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
            
            if item.quantity < instance.quantity:
                raise ValidationError(f"Stok {item.name} tidak cukup.")
            
            before = item.quantity
            item.quantity -= instance.quantity
            item.save()
            
            _create_inventory_log(item, -instance.quantity, before, item.quantity,
                                "TRANSACTION_ITEM_ADDED", instance.transaction.pk, 
                                f"Tambah item di Invoice {instance.transaction.invoice_number}")
    
    # Jika item diupdate (ganti item atau ubah quantity)
    else:
        old_item_id = getattr(instance, "_old_item_id", None)
        old_quantity = getattr(instance, "_old_quantity", None)
        
        if old_item_id is None:
            return
        
        with transaction.atomic():
            # Jika item diganti (beda item)
            if old_item_id != instance.item.pk:
                # Kembalikan stok item lama
                old_item = InventoryItem.objects.select_for_update().get(pk=old_item_id)
                before_old = old_item.quantity
                old_item.quantity += old_quantity
                old_item.save()
                
                _create_inventory_log(old_item, old_quantity, before_old, old_item.quantity,
                                    "TRANSACTION_ITEM_CHANGED", instance.transaction.pk,
                                    f"Item diganti di Invoice {instance.transaction.invoice_number}")
                
                # Kurangi stok item baru
                new_item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                
                if new_item.quantity < instance.quantity:
                    raise ValidationError(f"Stok {new_item.name} tidak cukup.")
                
                before_new = new_item.quantity
                new_item.quantity -= instance.quantity
                new_item.save()
                
                _create_inventory_log(new_item, -instance.quantity, before_new, new_item.quantity,
                                    "TRANSACTION_ITEM_CHANGED", instance.transaction.pk,
                                    f"Item baru di Invoice {instance.transaction.invoice_number}")
            
            # Jika hanya quantity yang berubah
            elif old_quantity != instance.quantity:
                item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                difference = instance.quantity - old_quantity
                
                if difference > 0 and item.quantity < difference:
                    raise ValidationError(f"Stok {item.name} tidak cukup untuk menambah quantity.")
                
                before = item.quantity
                item.quantity -= difference  # Bisa positif atau negatif
                item.save()
                
                _create_inventory_log(item, -difference, before, item.quantity,
                                    "TRANSACTION_ITEM_QTY_CHANGED", instance.transaction.pk,
                                    f"Ubah qty di Invoice {instance.transaction.invoice_number}")


@receiver(pre_delete, sender=TransactionItem)
def handle_transaction_item_delete(sender, instance, **kwargs):
    """Kembalikan stok jika item dihapus dari transaksi COMPLETED"""
    
    # Hanya proses jika transaksi sudah COMPLETED
    if instance.transaction.status != Transaction.StatusChoices.COMPLETED:
        return
    
    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        item.quantity += instance.quantity
        item.save()
        
        _create_inventory_log(item, instance.quantity, before, item.quantity,
                            "TRANSACTION_ITEM_DELETED", instance.transaction.pk,
                            f"Hapus item dari Invoice {instance.transaction.invoice_number}")


# ========== TOTAL CALCULATION ==========

# 4. Hitung Ulang Total Harga (Setiap kali Item/Service ditambah/hapus)
@receiver([post_save, post_delete], sender=TransactionItem)
@receiver([post_save, post_delete], sender=TransactionService)
def update_transaction_total(sender, instance, **kwargs):
    txn = instance.transaction
    items_total = sum(item.subtotal for item in txn.items.all())
    services_total = sum(svc.subtotal for svc in txn.services.all())
   
    grand_total = items_total + services_total + txn.other_charges - txn.discount_amount
    Transaction.objects.filter(pk=txn.pk).update(total_amount=grand_total)