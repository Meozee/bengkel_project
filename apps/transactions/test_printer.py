# test_printer.py
from escpos.printer import Usb

try:
    print("🔌 Menghubungkan ke printer...")
    p = Usb(0x0483, 0x070b, 0, profile="TM-T88II")
    p.text("✅ TEST CETAK BERHASIL!\n")
    p.text("Jika teks ini muncul, printer siap dipakai.\n")
    p.cut()
    print("🖨️  Cetak sukses!")
except Exception as e:
    print(f"❌ Gagal: {e}")