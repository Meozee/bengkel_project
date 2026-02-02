# apps/transactions/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Transaction, TransactionItem, TransactionItemSource # Tambah TransactionItemSource
from apps.purchases.models import PurchaseOrderItem # Tambah ini
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
    if created: return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # === KASUS 1: PENDING -> COMPLETED (LOGIK FIFO) ===
    if old_status != Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.COMPLETED:
        with transaction.atomic():
            Transaction.objects.filter(pk=instance.pk).update(completed_at=timezone.now())

            for tx_item in instance.items.all():
                qty_needed = tx_item.quantity
                
                # Cari batch PO yang statusnya COMPLETED dan stoknya masih ada
                batches = PurchaseOrderItem.objects.filter(
                    item=tx_item.item,
                    quantity_remaining__gt=0,
                    purchase_order__status='COMPLETED'
                ).order_by('purchase_order__order_date')

                for batch in batches:
                    if qty_needed <= 0: break
                    
                    if batch.quantity_remaining >= qty_needed:
                        take = qty_needed
                        batch.quantity_remaining -= take
                        qty_needed = 0
                    else:
                        take = batch.quantity_remaining
                        qty_needed -= take
                        batch.quantity_remaining = 0
                    
                    batch.save()
                    TransactionItemSource.objects.create(
                        transaction_item=tx_item,
                        purchase_order_item=batch,
                        quantity_taken=take
                    )

                # --- KUNCI PERBAIKAN 2: Validasi Ketat ---
                if qty_needed > 0:
                    raise ValueError(
                        f"Gagal! Stok batch untuk {tx_item.item.name} tidak cukup. "
                        f"Kurang {qty_needed} unit di catatan PO. "
                        f"Pastikan semua PO sudah COMPLETED sebelum transaksi selesai."
                    )

                # Update total master inventory (tetap perlu untuk tampilan stok cepat)
                inv = InventoryItem.objects.select_for_update().get(pk=tx_item.item.pk)
                before = inv.quantity
                inv.quantity = max(0, before - tx_item.quantity)
                inv.save()

                _create_inventory_log(inv, -tx_item.quantity, before, inv.quantity, 
                                     "TRANSACTION_COMPLETED", instance.pk, 
                                     f"FIFO Out: {instance.invoice_number}")

    # === KASUS 2: COMPLETED -> CANCELLED (LOGIK RESTORE) ===
    elif old_status == Transaction.StatusChoices.COMPLETED and new_status == Transaction.StatusChoices.CANCELLED:
        with transaction.atomic():
            for tx_item in instance.items.all():
                # Kembalikan ke batch PO asal (LIFO untuk pembatalan)
                sources = TransactionItemSource.objects.filter(transaction_item=tx_item)
                for src in sources:
                    po_item = src.purchase_order_item
                    po_item.quantity_remaining += src.quantity_taken
                    po_item.save()
                
                # Update master inventory
                inv = InventoryItem.objects.select_for_update().get(pk=tx_item.item.pk)
                before = inv.quantity
                inv.quantity += tx_item.quantity
                inv.save()
                
                _create_inventory_log(inv, tx_item.quantity, before, inv.quantity, 
                                     "TRANSACTION_CANCELLED", instance.pk)

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