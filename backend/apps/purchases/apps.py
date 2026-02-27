from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.purchases'
    verbose_name = _("إدارة المشتريات")

    def ready(self):
        # By importing the signals module, the __init__.py will load all specific signal files
        import apps.purchases.signals