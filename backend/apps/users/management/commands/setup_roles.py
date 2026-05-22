from django.core.management.base import BaseCommand

from apps.users.roles import SYSTEM_ROLES, create_default_groups


class Command(BaseCommand):
    help = "Create the standard ERP authorization roles."

    def handle(self, *args, **kwargs):
        created_count = create_default_groups()
        self.stdout.write(
            self.style.SUCCESS(
                f"ERP roles ready: {len(SYSTEM_ROLES)} roles, "
                f"{created_count} newly created."
            )
        )
