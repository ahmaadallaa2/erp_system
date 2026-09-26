from django.db import migrations


def fix_cash_bank_reconciliation_flags(apps, schema_editor):
    Account = apps.get_model("accounting", "Account")

    Account.objects.filter(
        code__in=["1001", "1002"],
        is_deleted=False,
        allow_reconciliation=True,
    ).update(allow_reconciliation=False)


class Migration(migrations.Migration):

    dependencies = [
        ("accounting", "0005_seed_standard_chart_of_accounts"),
    ]

    operations = [
        migrations.RunPython(
            fix_cash_bank_reconciliation_flags,
            reverse_code=migrations.RunPython.noop,
        ),
    ]
