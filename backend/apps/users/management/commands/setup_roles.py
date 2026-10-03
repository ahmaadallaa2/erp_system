from django.core.management.base import BaseCommand

from apps.users.roles import SYSTEM_ROLES, sync_role_groups


class Command(BaseCommand):
    help = (
        "Re-sync the standard ERP role groups and their model permissions. "
        "This already runs automatically after every `migrate`; use it only to "
        "restore groups or permissions that were removed manually."
    )

    def handle(self, *args, **kwargs):
        created_count = sync_role_groups()
        self.stdout.write(
            self.style.SUCCESS(
                f"ERP roles ready: {len(SYSTEM_ROLES)} roles, "
                f"{created_count} newly created."
            )
        )
