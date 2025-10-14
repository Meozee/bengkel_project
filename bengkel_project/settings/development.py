# bengkel_project/settings/development.py

# Impor semua settingan dari base.py
from .base import *

# Settingan khusus untuk mode development

# Izinkan semua host saat development
ALLOWED_HOSTS = ['*']

# Di sini kita bisa menambahkan settingan lain khusus development,
# misalnya jika kita menggunakan database yang berbeda untuk testing.
# Untuk sekarang, ini sudah cukup.

print("Development settings loaded.") # Pesan ini untuk memastikan file ini yang dipakai