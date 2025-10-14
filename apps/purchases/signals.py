# apps/purchases/signals.py

from decimal import Decimal
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from .models import PurchaseOrder, PurchaseOrderItem
from apps.inventory.models import InventoryItem, InventoryLog

# --- UTILITY ---
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


# --- SIMpan OLD STATUS sebelum save PurchaseOrder ---
@receiver(pre_save, sender=PurchaseOrder)
def store_old_purchase_status(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = PurchaseOrder.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except PurchaseOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


# --- SIMpan OLD QUANTITY sebelum save PurchaseOrderItem ---
@receiver(pre_save, sender=PurchaseOrderItem)
def store_old_po_item_quantity(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_item = PurchaseOrderItem.objects.get(pk=instance.pk)
            instance._old_quantity = old_item.quantity
            instance._old_unit_price = old_item.unit_price
        except PurchaseOrderItem.DoesNotExist:
            instance._old_quantity = 0
            instance._old_unit_price = Decimal('0.00')
    else:
        instance._old_quantity = 0
        instance._old_unit_price = Decimal('0.00')


# --- Update total_amount pada PO ketika item dibuat/di-update/dihapus ---
@receiver([post_save, post_delete], sender=PurchaseOrderItem)
def update_purchase_order_total(sender, instance, **kwargs):
    purchase_order = instance.purchase_order
    total_items_price = sum(item.subtotal for item in purchase_order.items.all())
    PurchaseOrder.objects.filter(pk=purchase_order.pk).update(total_amount=total_items_price)


# --- Saat item PO disimpan: jika PO sudah COMPLETED maka adjust stok berdasarkan delta ---
@receiver(post_save, sender=PurchaseOrderItem)
def adjust_stock_when_po_item_saved(sender, instance, created, **kwargs):
    po = instance.purchase_order
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return  # hanya berlaku saat PO COMPLETED

    # hitung selisih
    old_q = getattr(instance, '_old_quantity', 0)
    delta = instance.quantity - old_q

    if delta == 0:
        return

    # lakukan update atomic + lock row item
    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        item.quantity = item.quantity + delta
        # update buy_price weighted average: hanya jika delta > 0 (penambahan stok dari PO)
        if delta > 0:
            old_stock_value = Decimal(before) * Decimal(item.buy_price)
            new_stock_value = Decimal(delta) * Decimal(instance.unit_price)
            total_qty = before + delta
            if total_qty > 0:
                item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)
        item.save()

        _create_inventory_log(
            item=item,
            change=delta,
            before=before,
            after=item.quantity,
            source_type="PURCHASE_ITEM_EDIT",
            source_id=po.pk,
            note=f"POItem#{instance.pk} edited (created={created})"
        )


# --- Saat item PO dihapus: kurangi stok jika PO COMPLETED ---
@receiver(post_delete, sender=PurchaseOrderItem)
def adjust_stock_when_po_item_deleted(sender, instance, **kwargs):
    po = instance.purchase_order
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        # jangan buat negatif — jika kurang, set 0
        new_qty = max(0, item.quantity - instance.quantity)
        change = new_qty - before
        item.quantity = new_qty
        item.save()

        _create_inventory_log(
            item=item,
            change=change,
            before=before,
            after=new_qty,
            source_type="PURCHASE_ITEM_DELETE",
            source_id=po.pk,
            note=f"POItem#{instance.pk} deleted"
        )


# --- Saat status PO berubah: handle transisi lengkap ---
@receiver(post_save, sender=PurchaseOrder)
def handle_stock_on_purchase_status_change(sender, instance, created, **kwargs):
    """
    Ada 3 kondisi utama:
      - masuk ke COMPLETED (old != COMPLETED and new == COMPLETED): tambahkan semua item PO
      - keluar dari COMPLETED (old == COMPLETED and new != COMPLETED): kurangi semua item PO
      - selain itu: no-op
    """

    old_status = getattr(instance, "_old_status", None)

    # jika baru dibuat dan langsung COMPLETED -> treat as transition to COMPLETED
    became_completed = (old_status != PurchaseOrder.StatusChoices.COMPLETED and instance.status == PurchaseOrder.StatusChoices.COMPLETED)
    left_completed = (old_status == PurchaseOrder.StatusChoices.COMPLETED and instance.status != PurchaseOrder.StatusChoices.COMPLETED)

    if not (became_completed or left_completed):
        return

    with transaction.atomic():
        # lock semua inventory items involved
        item_ids = instance.items.values_list('item_id', flat=True).distinct()
        items_map = {
            it.pk: InventoryItem.objects.select_for_update().get(pk=it.pk)
            for it in InventoryItem.objects.filter(pk__in=item_ids)
        }

        if became_completed:
            # tambah stok dan update buy_price weighted avg
            for order_item in instance.items.all():
                item = items_map[order_item.item_id]
                before = item.quantity
                delta = order_item.quantity
                old_stock_value = Decimal(before) * Decimal(item.buy_price)
                new_stock_value = Decimal(delta) * Decimal(order_item.unit_price)
                total_qty = before + delta
                if total_qty > 0:
                    item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)
                item.quantity = total_qty
                item.save()

                _create_inventory_log(
                    item=item,
                    change=delta,
                    before=before,
                    after=item.quantity,
                    source_type="PURCHASE",
                    source_id=instance.pk,
                    note=f"PO#{instance.pk} completed"
                )

        elif left_completed:
            # batalkan penambahan stok sebelumnya -> kurangi
            for order_item in instance.items.all():
                item = items_map[order_item.item_id]
                before = item.quantity
                # hindari negatif
                new_qty = max(0, item.quantity - order_item.quantity)
                change = new_qty - before  # negative or zero
                item.quantity = new_qty
                item.save()

                _create_inventory_log(
                    item=item,
                    change=change,
                    before=before,
                    after=new_qty,
                    source_type="PURCHASE_CANCEL",
                    source_id=instance.pk,
                    note=f"PO#{instance.pk} left COMPLETED"
                )
