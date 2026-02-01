import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from faker import Faker
from decimal import Decimal

# Import semua model sesuai strukturmu
from apps.accounts.models import CustomUser
from apps.master_data.models import Mechanic, Customer, Vehicle, Service, Vendor
from apps.inventory.models import Category, InventoryItem
from apps.expenses.models import ExpenseCategory, Expense
from apps.transactions.models import Transaction, TransactionItem, TransactionService
from apps.purchases.models import PurchaseOrder, PurchaseOrderItem

class Command(BaseCommand):
    help = "Seed data untuk stress testing bengkel"

    def add_arguments(self, parser):
        parser.add_argument('n', type=int, help='Jumlah transaksi yang ingin dibuat')

    def handle(self, *args, **kwargs):
        n = kwargs['n']
        fake = Faker(['id_ID'])
        self.stdout.write("Memulai proses seeding...")

        # 1. Buat Master Data Dasar (Jika belum ada)
        self.stdout.write("- Membuat Master Data...")
        mechanics = [Mechanic.objects.create(name=fake.name(), specialty="General") for _ in range(5)]
        vendors = [Vendor.objects.create(name=fake.company()) for _ in range(3)]
        categories = [Category.objects.create(name=fake.word().capitalize()) for _ in range(5)]
        services = [Service.objects.create(name=f"Service {fake.word()}", price=random.randint(50000, 200000)) for _ in range(10)]
        exp_cat = ExpenseCategory.objects.create(name="Operasional")

        # 2. Buat Inventory Items
        self.stdout.write("- Membuat Inventory...")
        items = []
        for _ in range(20):
            items.append(InventoryItem.objects.create(
                category=random.choice(categories),
                name=fake.bs().capitalize(),
                sku=fake.unique.ean8(),
                buy_price=Decimal(random.randint(5000, 50000)),
                sell_price=Decimal(random.randint(60000, 150000)),
                quantity=random.randint(10, 100)
            ))

        # 3. Buat Pelanggan & Kendaraan
        self.stdout.write("- Membuat Pelanggan...")
        customers = []
        for _ in range(n // 2): # Rasio 1 pelanggan untuk 2 transaksi
            cust = Customer.objects.create(
                name=fake.name(),
                phone_number=fake.unique.phone_number()
            )
            Vehicle.objects.create(
                customer=cust,
                license_plate=fake.unique.license_plate(),
                brand=random.choice(['Toyota', 'Honda', 'Suzuki']),
                model=fake.word().capitalize()
            )
            customers.append(cust)

        # 4. LOOP UTAMA: Transaksi (Data yang paling banyak)
        self.stdout.write(f"- Membuat {n} Transaksi...")
        for i in range(n):
            cust = random.choice(customers)
            veh = cust.vehicles.first()
            mech = random.choice(mechanics)

            # Buat Header Transaksi
            txn = Transaction.objects.create(
                customer=cust,
                vehicle=veh,
                mechanic=mech,
                status=Transaction.StatusChoices.COMPLETED,
                notes=fake.sentence()
            )

            # Isi Barang (1-3 barang per transaksi)
            for _ in range(random.randint(1, 3)):
                item = random.choice(items)
                qty = random.randint(1, 2)
                TransactionItem.objects.create(
                    transaction=txn,
                    item=item,
                    quantity=qty,
                    unit_price=item.sell_price
                )

            # Isi Jasa (1-2 jasa per transaksi)
            for _ in range(random.randint(1, 2)):
                svc = random.choice(services)
                TransactionService.objects.create(
                    transaction=txn,
                    service=svc,
                    unit_price=svc.price
                )
            
            # Update total_amount transaksi sederhana
            # (Jika kamu punya logic kalkulasi di save/property, ini bisa di skip)
            if i % 100 == 0:
                self.stdout.write(f"Telah memproses {i} data...")

        self.stdout.write(self.style.SUCCESS(f"Selesai! Berhasil menyuntikkan data massal."))