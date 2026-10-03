from django.apps import AppConfig
from django.db.models.signals import post_migrate


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = "إدارة المستخدمين"

    def ready(self):
        from apps.users.signals import sync_roles_after_migrate

        post_migrate.connect(
            sync_roles_after_migrate,
            dispatch_uid="users_sync_role_groups",
        )
