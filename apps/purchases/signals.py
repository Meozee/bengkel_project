# apps/purchases/signals.py

from decimal import Decimal
from django.db import transaction
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from .models import PurchaseOrder, PurchaseOrderItem
from apps.inventory.models import InventoryItem, InventoryLog


# ========== UTILITY ==========

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


# ========== PURCHASE ORDER STATUS HANDLING ==========

@receiver(pre_save, sender=PurchaseOrder)
def store_old_purchase_status(sender, instance, **kwargs):
    """Simpan status lama untuk deteksi perubahan"""
    if instance.pk:
        try:
            old = PurchaseOrder.objects.get(pk=instance.pk)
            instance._old_status = old.status
        except PurchaseOrder.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=PurchaseOrder)
def handle_purchase_status_change(sender, instance, created, **kwargs):
    """
    Handle perubahan status Purchase Order:
    - PENDING/CANCELLED → COMPLETED: tambah stok + update buy_price
    - COMPLETED → CANCELLED: kurangi stok kembali
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # Transisi menjadi COMPLETED
    if old_status != PurchaseOrder.StatusChoices.COMPLETED and new_status == PurchaseOrder.StatusChoices.COMPLETED:
        with transaction.atomic():
            # Lock semua inventory items yang terlibat
            item_ids = instance.items.values_list('item_id', flat=True).distinct()
            items_map = {
                it.pk: InventoryItem.objects.select_for_update().get(pk=it.pk)
                for it in InventoryItem.objects.filter(pk__in=item_ids)
            }

            # Tambah stok dan update buy_price (weighted average)
            for po_item in instance.items.all():
                item = items_map[po_item.item_id]
                before = item.quantity
                delta = po_item.quantity

                # Update buy_price menggunakan weighted average
                old_stock_value = Decimal(before) * Decimal(item.buy_price)
                new_stock_value = Decimal(delta) * Decimal(po_item.unit_price)
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
                    source_type="PURCHASE_COMPLETED",
                    source_id=instance.pk,
                    note=f"PO #{instance.pk} completed"
                )

    # Transisi keluar dari COMPLETED (biasanya ke CANCELLED)
    elif old_status == PurchaseOrder.StatusChoices.COMPLETED and new_status != PurchaseOrder.StatusChoices.COMPLETED:
        with transaction.atomic():
            item_ids = instance.items.values_list('item_id', flat=True).distinct()
            items_map = {
                it.pk: InventoryItem.objects.select_for_update().get(pk=it.pk)
                for it in InventoryItem.objects.filter(pk__in=item_ids)
            }

            # Kurangi stok kembali
            for po_item in instance.items.all():
                item = items_map[po_item.item_id]
                before = item.quantity
                # Hindari stok negatif
                new_qty = max(0, item.quantity - po_item.quantity)
                change = new_qty - before

                item.quantity = new_qty
                item.save()

                _create_inventory_log(
                    item=item,
                    change=change,
                    before=before,
                    after=new_qty,
                    source_type="PURCHASE_CANCELLED",
                    source_id=instance.pk,
                    note=f"PO #{instance.pk} cancelled/reverted"
                )


# ========== PURCHASE ORDER ITEM HANDLING ==========

@receiver(pre_save, sender=PurchaseOrderItem)
def store_old_po_item(sender, instance, **kwargs):
    """Simpan data item lama untuk deteksi perubahan"""
    if instance.pk:
        try:
            old_item = PurchaseOrderItem.objects.get(pk=instance.pk)
            instance._old_item_id = old_item.item.pk
            instance._old_quantity = old_item.quantity
            instance._old_unit_price = old_item.unit_price
        except PurchaseOrderItem.DoesNotExist:
            instance._old_item_id = None
            instance._old_quantity = 0
            instance._old_unit_price = Decimal('0.00')
    else:
        instance._old_item_id = None
        instance._old_quantity = 0
        instance._old_unit_price = Decimal('0.00')


@receiver(post_save, sender=PurchaseOrderItem)
def handle_po_item_change(sender, instance, created, **kwargs):
    """
    Handle perubahan item dalam PO yang sudah COMPLETED:
    - Item baru ditambahkan → tambah stok
    - Item diganti → kembalikan stok item lama, tambah stok item baru
    - Quantity diubah → adjust stok sesuai delta
    """
    po = instance.purchase_order

    # Hanya proses jika PO sudah COMPLETED
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    # Jika item baru ditambahkan ke PO yang sudah COMPLETED
    if created:
        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
            before = item.quantity
            delta = instance.quantity

            # Update buy_price weighted average
            old_stock_value = Decimal(before) * Decimal(item.buy_price)
            new_stock_value = Decimal(delta) * Decimal(instance.unit_price)
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
                source_type="PURCHASE_ITEM_ADDED",
                source_id=po.pk,
                note=f"Item ditambahkan ke PO #{po.pk}"
            )

    # Jika item diupdate (ganti item atau ubah quantity)
    else:
        old_item_id = getattr(instance, "_old_item_id", None)
        old_quantity = getattr(instance, "_old_quantity", 0)
        old_unit_price = getattr(instance, "_old_unit_price", Decimal('0.00'))

        if old_item_id is None:
            return

        with transaction.atomic():
            # Jika item diganti (beda item)
            if old_item_id != instance.item.pk:
                # Kurangi stok item lama
                old_item = InventoryItem.objects.select_for_update().get(pk=old_item_id)
                before_old = old_item.quantity
                new_qty_old = max(0, old_item.quantity - old_quantity)
                change_old = new_qty_old - before_old

                old_item.quantity = new_qty_old
                old_item.save()

                _create_inventory_log(
                    old_item, change_old, before_old, new_qty_old,
                    "PURCHASE_ITEM_CHANGED", po.pk,
                    f"Item diganti di PO #{po.pk}"
                )

                # Tambah stok item baru
                new_item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                before_new = new_item.quantity
                delta_new = instance.quantity

                # Update buy_price weighted average
                old_stock_value = Decimal(before_new) * Decimal(new_item.buy_price)
                new_stock_value = Decimal(delta_new) * Decimal(instance.unit_price)
                total_qty = before_new + delta_new

                if total_qty > 0:
                    new_item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)

                new_item.quantity = total_qty
                new_item.save()

                _create_inventory_log(
                    new_item, delta_new, before_new, new_item.quantity,
                    "PURCHASE_ITEM_CHANGED", po.pk,
                    f"Item baru di PO #{po.pk}"
                )

            # Jika hanya quantity atau price yang berubah
            elif old_quantity != instance.quantity or old_unit_price != instance.unit_price:
                item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                before = item.quantity
                delta = instance.quantity - old_quantity

                if delta != 0:
                    # Update buy_price jika ada perubahan quantity atau price
                    if delta > 0:  # Penambahan stok
                        old_stock_value = Decimal(before) * Decimal(item.buy_price)
                        new_stock_value = Decimal(delta) * Decimal(instance.unit_price)
                        total_qty = before + delta
                        if total_qty > 0:
                            item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)
                    # Jika pengurangan, buy_price tidak perlu diupdate

                    item.quantity = before + delta
                    item.save()

                    _create_inventory_log(
                        item, delta, before, item.quantity,
                        "PURCHASE_ITEM_QTY_CHANGED", po.pk,
                        f"Qty diubah di PO #{po.pk}"
                    )


@receiver(pre_delete, sender=PurchaseOrderItem)
def handle_po_item_delete(sender, instance, **kwargs):
    """Kurangi stok jika item dihapus dari PO COMPLETED"""
    po = instance.purchase_order

    # Hanya proses jika PO sudah COMPLETED
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        # Hindari stok negatif
        new_qty = max(0, item.quantity - instance.quantity)
        change = new_qty - before

        item.quantity = new_qty
        item.save()

        _create_inventory_log(
            item, change, before, new_qty,
            "PURCHASE_ITEM_DELETED", po.pk,
            f"Item dihapus dari PO #{po.pk}"
        )


# ========== TOTAL CALCULATION ==========

@receiver([post_save, post_delete], sender=PurchaseOrderItem)
def update_purchase_order_total(sender, instance, **kwargs):
    """Hitung ulang total PO setiap kali item berubah"""
    po = instance.purchase_order
    total_items_price = sum(item.subtotal for item in po.items.all())
    PurchaseOrder.objects.filter(pk=po.pk).update(total_amount=total_items_price)