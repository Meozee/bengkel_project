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
    """
    Handle perubahan status Purchase Order:
    - PENDING/CANCELLED → COMPLETED: tambah stok + update buy_price
    - COMPLETED → CANCELLED: kurangi stok kembali (DENGAN VALIDASI)
    """
    if created:
        return

    old_status = getattr(instance, "_old_status", None)
    new_status = instance.status

    # === KASUS 1: Transaksi Selesai (Barang Masuk) ===
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
                po_item.quantity_remaining = po_item.quantity 
                po_item.save()
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

    # === KASUS 2: Pembatalan PO (Barang Keluar/Ditarik) ===
    elif old_status == PurchaseOrder.StatusChoices.COMPLETED and new_status != PurchaseOrder.StatusChoices.COMPLETED:
        
        # [NEW LOGIC] VALIDASI STOK SEBELUM CANCEL
        # Cek apakah stok cukup untuk ditarik kembali?
        for po_item in instance.items.all():
            current_stock = po_item.item.quantity
            qty_to_remove = po_item.quantity
            
            # Jika stok gudang LEBIH KECIL dari yang mau ditarik, artinya barang sudah terjual
            if current_stock < qty_to_remove:
                # Raise ValueError ini akan ditangkap oleh views.py dan ditampilkan sebagai pesan error ke user
                raise ValueError(
                    f"GAGAL: Barang '{po_item.item.name}' sisa stok {current_stock}, "
                    f"padahal PO mencatat {qty_to_remove}. Sebagian barang sudah terjual!"
                )

        # Jika lolos validasi di atas, baru jalankan pengurangan stok
        with transaction.atomic():
            item_ids = instance.items.values_list('item_id', flat=True).distinct()
            items_map = {
                it.pk: InventoryItem.objects.select_for_update().get(pk=it.pk)
                for it in InventoryItem.objects.filter(pk__in=item_ids)
            }

            for po_item in instance.items.all():
                item = items_map[po_item.item_id]
                before = item.quantity
                
                # Kurangi stok (Pasti aman karena sudah divalidasi diatas)
                new_qty = item.quantity - po_item.quantity
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
    Handle perubahan item dalam PO yang sudah COMPLETED.
    """
    po = instance.purchase_order

    # Hanya proses jika PO sudah COMPLETED
    if po.status != PurchaseOrder.StatusChoices.COMPLETED:
        return

    # [NOTE] Logic ini jarang terpanggil jika UI sudah memblokir edit PO Completed.
    # Namun tetap kita pertahankan untuk keamanan level database.

    if created:
        with transaction.atomic():
            item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
            before = item.quantity
            delta = instance.quantity

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

    else:
        old_item_id = getattr(instance, "_old_item_id", None)
        old_quantity = getattr(instance, "_old_quantity", 0)
        old_unit_price = getattr(instance, "_old_unit_price", Decimal('0.00'))

        if old_item_id is None:
            return

        with transaction.atomic():
            # Logic sederhana: Update item yang ada
            if old_item_id == instance.item.pk:
                item = InventoryItem.objects.select_for_update().get(pk=instance.item.pk)
                before = item.quantity
                delta = instance.quantity - old_quantity

                if delta != 0:
                    if delta > 0:
                        old_stock_value = Decimal(before) * Decimal(item.buy_price)
                        new_stock_value = Decimal(delta) * Decimal(instance.unit_price)
                        total_qty = before + delta
                        if total_qty > 0:
                            item.buy_price = (old_stock_value + new_stock_value) / Decimal(total_qty)

                    item.quantity = before + delta
                    item.save()

                    _create_inventory_log(
                        item=item, delta=delta, before=before, after=item.quantity,
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