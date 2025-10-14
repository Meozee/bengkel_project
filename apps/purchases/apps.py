# apps/purchases/apps.py

from django.apps import AppConfig

class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchases'

    def ready(self):
        # Impor signals secara implisit saat aplikasi siap
        import apps.purchases.signals