from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounting.services.chart_of_accounts_seed import (
    create_default_chart_of_accounts,
)
from apps.core.models.company import Company


@receiver(post_save, sender=Company, dispatch_uid="accounting_create_default_coa")
def create_default_chart_of_accounts_for_new_company(sender, instance, created, raw=False, **kwargs):
    # raw=True during loaddata: fixtures supply their own accounts.
    if not created or raw:
        return

    create_default_chart_of_accounts(instance)
