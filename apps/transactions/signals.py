# apps/transactions/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Transaction, TransactionItem
from apps.inventory.models import InventoryItem, InventoryLog

# ========== UTILITY ==========
def _create_inventory_log(item, change, before, after, source_type, source_id, note=""):
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

@receiver(pre_save, sender=Transaction)
def store_old_transaction_status(sender, instance, **kwargs):
    """Simpan status lama sebelum save untuk deteksi perubahan"""
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Transaction.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Transaction)
def handle_transaction_status_change(sender, instance, created, **kwargs):
    """
    Logika Stok:
    1. PENDING -> COMPLETED: KURANGI stok (Barang keluar)
    2. COMPLETED -> CANCELLED: KEMBALIKAN stok (Barang batal jual)
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # === KASUS 1: Transaksi Selesai (PENDING -> COMPLETED) ===
    # Stok HARUS BERKURANG
    if old_status != Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.COMPLETED:
        with transaction.atomic():
            # Update waktu selesai
            Transaction.objects.filter(pk=instance.pk).update(completed_at=timezone.now())

            # Loop semua item di keranjang
            for tx_item in instance.items.all():
                # Lock row inventory biar aman
                inventory_item = InventoryItem.objects.select_for_update().get(pk=tx_item.item.pk)
                
                before_qty = inventory_item.quantity
                qty_sold = tx_item.quantity
                
                # Cek apakah stok cukup? (Opsional: bisa di-handle di form validation juga)
                # if before_qty < qty_sold:
                #    raise ValueError(f"Stok {inventory_item.name} tidak cukup!")

                # KURANGI STOK
                new_qty = max(0, before_qty - qty_sold)
                inventory_item.quantity = new_qty
                inventory_item.save()

                # CATAT LOG (Change negatif karena berkurang)
                _create_inventory_log(
                    item=inventory_item,
                    change=-qty_sold,  # Negatif
                    before=before_qty,
                    after=new_qty,
                    source_type="TRANSACTION_COMPLETED",
                    source_id=instance.pk,
                    note=f"Terjual di Invoice {instance.invoice_number}"
                )

    # === KASUS 2: Batal Selesai (COMPLETED -> CANCELLED) ===
    # Stok HARUS KEMBALI
    elif old_status == Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.CANCELLED:
        with transaction.atomic():
            for tx_item in instance.items.all():
                inventory_item = InventoryItem.objects.select_for_update().get(pk=tx_item.item.pk)
                
                before_qty = inventory_item.quantity
                qty_returned = tx_item.quantity

                # TAMBAH STOK KEMBALI
                new_qty = before_qty + qty_returned
                inventory_item.quantity = new_qty
                inventory_item.save()

                # CATAT LOG (Change positif karena kembali)
                _create_inventory_log(
                    item=inventory_item,
                    change=qty_returned, # Positif
                    before=before_qty,
                    after=new_qty,
                    source_type="TRANSACTION_CANCELLED",
                    source_id=instance.pk,
                    note=f"Pembatalan Invoice {instance.invoice_number}"
                )

# ========== UPDATE TOTAL AMOUNT OTOMATIS ==========

@receiver([post_save, post_delete], sender=TransactionItem)
def update_transaction_total(sender, instance, **kwargs):
    """
    Hitung ulang total_amount di header Transaction setiap kali item berubah.
    Hanya update jika status masih PENDING.
    """
    txn = instance.transaction
    
    # Jangan update total jika sudah completed/cancelled (karena data di-lock)
    if txn.status != Transaction.StatusChoices.PENDING:
        return

    total_items = sum(item.subtotal for item in txn.items.all())
    total_services = sum(svc.subtotal for svc in txn.services.all())
    
    # Hitung: (Item + Jasa + Lain2) - Diskon
    new_total = total_items + total_services + txn.other_charges - txn.discount_amount
    
    # Update pakai queryset update biar gak memicu infinite loop signal save transaction
    Transaction.objects.filter(pk=txn.pk).update(total_amount=new_total)