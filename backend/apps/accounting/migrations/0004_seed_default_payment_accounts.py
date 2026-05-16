from django.db import migrations


def seed_default_payment_accounts(apps, schema_editor):
    from apps.accounting.services.chart_of_accounts_seed import (
        seed_standard_chart_of_accounts,
    )

    Company = apps.get_model("core", "Company")
    Account = apps.get_model("accounting", "Account")

    for company in Company.objects.all():
        seed_standard_chart_of_accounts(company, account_model=Account)


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0003_initial"),
    ]

    operations = [
        migrations.RunPython(
            seed_default_payment_accounts,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
