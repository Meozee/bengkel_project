#apps/purchases/signals.py
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
    if created: return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # === KASUS 1: PENDING -> COMPLETED (Barang Masuk) ===
    if old_status != 'COMPLETED' and new_status == 'COMPLETED':
        with transaction.atomic():
            for po_item in instance.items.all():
                # 1. Inisialisasi Remaining (FIFO)
                po_item.quantity_remaining = po_item.quantity 
                po_item.save()
                
                # 2. Ambil Item Master
                item = InventoryItem.objects.select_for_update().get(pk=po_item.item.pk) # Pakai select_for_update biar aman
                before_qty = item.quantity
                
                # --- [PERBAIKAN UTAMA] HITUNG HARGA RATA-RATA (AVERAGE COST) ---
                # Rumus: (Nilai Stok Lama + Nilai Stok Baru) / Total Stok Baru
                old_stock_value = Decimal(before_qty) * Decimal(item.buy_price)
                new_stock_value = Decimal(po_item.quantity) * Decimal(po_item.unit_price)
                total_qty = before_qty + po_item.quantity

                if total_qty > 0:
                    # Update Harga Beli Baru
                    item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)

                # 3. Update Stok Master
                item.quantity = total_qty
                item.save()

                # 4. Buat Log
                _create_inventory_log(
                    item, 
                    po_item.quantity, 
                    before_qty, 
                    item.quantity, 
                    "PURCHASE_COMPLETED", 
                    instance.pk, 
                    note=f"PO #{instance.pk} Completed"
                )

    # === KASUS 2: COMPLETED -> CANCELLED (Batalkan & Reset FIFO) ===
    elif old_status == PurchaseOrder.StatusChoices.COMPLETED and new_status != PurchaseOrder.StatusChoices.COMPLETED:
        # Validasi stok cukup sudah ditangani di views.update_status
        with transaction.atomic():
            for po_item in instance.items.all():
                # BUG B FIXED: Reset sisa batch jadi 0 agar tidak ditarik FIFO transaksi
                po_item.quantity_remaining = 0
                po_item.save()

                item = InventoryItem.objects.select_for_update().get(pk=po_item.item_id)
                before = item.quantity
                
                # Kurangi stok global
                item.quantity = max(0, item.quantity - po_item.quantity)
                item.save()

                _create_inventory_log(
                    item=item, change=(item.quantity - before), before=before,
                    after=item.quantity, source_type="PURCHASE_CANCELLED",
                    source_id=instance.pk, note=f"PO #{instance.pk} reverted"
                )

@receiver(post_save, sender=PurchaseOrderItem)
def handle_po_item_change(sender, instance, created, **kwargs):
    po = instance.purchase_order
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    # KASUS: Item Baru Ditambahkan ke PO Completed
    if created:
        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
            before = item.quantity
            delta = instance.quantity

            # 1. Inisialisasi Remaining (PENTING!)
            instance.quantity_remaining = instance.quantity 
            instance.save()

            # Hitung Average Price
            old_stock_value = Decimal(before) * Decimal(item.buy_price)
            new_stock_value = Decimal(delta) * Decimal(instance.unit_price)
            total_qty = before + delta

            if total_qty > 0:
                item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)

            item.quantity = total_qty
            item.save()

            _create_inventory_log(
                item=item, change=delta, before=before, after=item.quantity,
                source_type="PURCHASE_ITEM_ADDED", source_id=po.pk,
                note=f"Item ditambahkan ke PO #{po.pk}"
            )

    # KASUS: Item Diedit (Qty Berubah)
    else:
        old_item_id = getattr(instance, "_old_item_id", None)
        old_quantity = getattr(instance, "_old_quantity", 0)

        if old_item_id == instance.item.pk:
            with transaction.atomic():
                item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                before = item.quantity
                diff = instance.quantity - old_quantity 

                if diff != 0:
                    # 1. Update Remaining Stock sesuai perubahan (PENTING!)
                    # Jika qty nambah 5, remaining juga nambah 5
                    # Note: Hati-hati jika diff negatif dan remaining sudah terpakai
                    instance.quantity_remaining = max(0, instance.quantity_remaining + diff)
                    instance.save()

                    # Update Average Price
                    if diff > 0:
                        old_stock_value = Decimal(before) * Decimal(item.buy_price)
                        new_stock_value = Decimal(diff) * Decimal(instance.unit_price)
                        total_qty = before + diff
                        if total_qty > 0:
                            item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)
                    
                    item.quantity = before + diff
                    item.save()

                    _create_inventory_log(
                        item=item, change=diff, before=before, after=item.quantity,
                        source_type="PURCHASE_ITEM_QTY_CHANGED", source_id=po.pk,
                        note=f"Qty diubah di PO #{po.pk}"
                    )

@receiver(pre_delete, sender=PurchaseOrderItem)
def handle_po_item_delete(sender, instance, **kwargs):
    """Kurangi stok jika item dihapus dari PO COMPLETED"""
    po = instance.purchase_order

    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    with transaction.atomic():
        item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
        before = item.quantity
        new_qty = max(0, item.quantity - instance.quantity)
        change = new_qty - before

        item.quantity = new_qty
        item.save()

        _create_inventory_log(
            item=item, change=change, before=before, after=new_qty,
            source_type="PURCHASE_ITEM_DELETED", source_id=po.pk,
            note=f"Item dihapus dari PO #{po.pk}"
        )


@receiver([post_save, post_delete], sender=PurchaseOrderItem)
def update_purchase_order_total(sender, instance, **kwargs):
    """Hitung ulang total PO setiap kali item berubah"""
    po = instance.purchase_order
    total_items_price = sum(item.subtotal for item in po.items.all())
    PurchaseOrder.objects.filter(pk=po.pk).update(total_amount=total_items_price)