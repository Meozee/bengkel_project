# apps/transactions/signals.py

from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from .models import Transaction, TransactionItem, TransactionService
from apps.inventory.models import InventoryItem, InventoryLog

# --- UTILITY LOG ---
def _create_inventory_log(item: InventoryItem, change: int, before: int, after: int, source_type: str, source_id: int = None, note: str = ""):
    InventoryLog.objects.create(
        item=item,
        change=change,
        before=before,
        after=after,
        source_type=source_type,
        source_id=source_id,
        note=note
    )


# --- SIMpan OLD STATUS sebelum save Transaction ---
@receiver(pre_save, sender=Transaction)
def store_old_transaction_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = Transaction.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except Transaction.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# --- SIMpan OLD QUANTITY sebelum save TransactionItem ---
@receiver(pre_save, sender=TransactionItem)
def store_old_transaction_item_quantity(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_item = TransactionItem.objects.get(pk=instance.pk)
            instance._old_quantity = old_item.quantity
            instance._old_unit_price = old_item.unit_price
        except TransactionItem.DoesNotExist:
            instance._old_quantity = 0
            instance._old_unit_price = 0
    else:
        instance._old_quantity = 0
        instance._old_unit_price = 0


# --- Update total_amount pada Transaction ketika item/service berubah ---
@receiver([post_save, post_delete], sender=TransactionItem)
@receiver([post_save, post_delete], sender=TransactionService)
def update_transaction_total(sender, instance, **kwargs):
    transaction_obj = instance.transaction
    total_items_price = sum(item.subtotal for item in transaction_obj.items.all())
    total_services_price = sum(service.subtotal for service in transaction_obj.services.all())
    sub_total = total_items_price + total_services_price
    final_total = sub_total + transaction_obj.other_charges - transaction_obj.discount_amount
    Transaction.objects.filter(pk=transaction_obj.pk).update(total_amount=final_total)


# --- Saat TransactionItem disimpan: jika transaction.status == PAID, kalkulasi delta dan adjust stok ---
@receiver(post_save, sender=TransactionItem)
def adjust_stock_when_transaction_item_saved(sender, instance, created, **kwargs):
    txn = instance.transaction
    if txn.status != Transaction.StatusChoices.PAID:
        return  # hanya saat PAID

    old_q = getattr(instance, '_old_quantity', 0)
    delta = instance.quantity - old_q  # positive => butuh kurangi stok lebih banyak

    if delta == 0:
        return

    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        if delta > 0:
            # butuh kurangi stok; pastikan cukup
            if item.quantity < delta:
                raise ValidationError(f"Stok untuk {item.name} tidak mencukupi. Sisa {item.quantity}, dibutuhkan tambahan {delta}")
            item.quantity = item.quantity - delta
        else:
            # delta < 0 => jumlah berkurang -> kembalikan stok (-delta)
            item.quantity = item.quantity - delta  # subtract negative = add
        item.save()

        _create_inventory_log(
            item=item,
            change=-delta if delta>0 else -delta,  # jika delta>0, stok turun => negative change; if delta<0, stok naik
            before=before,
            after=item.quantity,
            source_type="TRANSACTION_ITEM_EDIT",
            source_id=txn.pk,
            note=f"TxnItem#{instance.pk} edited (created={created})"
        )


# --- Saat TransactionItem dihapus: jika transaction.status == PAID -> kembalikan stok ---
@receiver(post_delete, sender=TransactionItem)
def return_stock_when_transaction_item_deleted(sender, instance, **kwargs):
    txn = instance.transaction
    if txn.status != Transaction.StatusChoices.PAID:
        return

    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        item.quantity = item.quantity + instance.quantity
        item.save()

        _create_inventory_log(
            item=item,
            change=instance.quantity,
            before=before,
            after=item.quantity,
            source_type="TRANSACTION_ITEM_DELETE",
            source_id=txn.pk,
            note=f"TxnItem#{instance.pk} deleted"
        )


# --- Saat status Transaction berubah: handle transisi PAID <-> non-PAID ---
@receiver(post_save, sender=Transaction)
def handle_stock_on_transaction_status_change(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    became_paid = (old_status != Transaction.StatusChoices.PAID and instance.status == Transaction.StatusChoices.PAID)
    left_paid = (old_status == Transaction.StatusChoices.PAID and instance.status != Transaction.StatusChoices.PAID)

    if not (became_paid or left_paid):
        return

    with transaction.atomic():
        # lock inventory rows
        item_ids = instance.items.values_list('item_id', flat=True).distinct()
        items_map = {
            it.pk: InventoryItem.objects.select_for_update().get(pk=it.pk)
            for it in InventoryItem.objects.filter(pk__in=item_ids)
        }

        if became_paid:
            # kurangi stok sesuai item quantity, pastikan seluruh stok cukup
            for detail in instance.items.all():
                item = items_map[detail.item_id]
                if item.quantity < detail.quantity:
                    # rollback otomatis karena atomic -> raise error
                    raise ValidationError(f"Tidak bisa mengubah status ke PAID. Stok {item.name} tidak cukup (tersisa {item.quantity}, diperlukan {detail.quantity}).")
            # jika semua cukup, baru kurangi
            for detail in instance.items.all():
                item = items_map[detail.item_id]
                before = item.quantity
                item.quantity = item.quantity - detail.quantity
                item.save()
                _create_inventory_log(
                    item=item,
                    change=-detail.quantity,
                    before=before,
                    after=item.quantity,
                    source_type="TRANSACTION",
                    source_id=instance.pk,
                    note=f"Txn#{instance.pk} marked PAID"
                )

        elif left_paid:
            # kembalikan stok
            for detail in instance.items.all():
                item = items_map[detail.item_id]
                before = item.quantity
                item.quantity = item.quantity + detail.quantity
                item.save()
                _create_inventory_log(
                    item=item,
                    change=detail.quantity,
                    before=before,
                    after=item.quantity,
                    source_type="TRANSACTION_CANCEL",
                    source_id=instance.pk,
                    note=f"Txn#{instance.pk} left PAID"
                )
