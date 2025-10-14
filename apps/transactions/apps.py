# apps/transactions/apps.py

from django.apps import AppConfig

class TransactionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.transactions'

    def ready(self):
        # Impor signals secara implisit saat aplikasi siap
        import apps.transactions.signals