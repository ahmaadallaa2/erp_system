from django.apps import apps as global_apps
from django.db import DEFAULT_DB_ALIAS, router

from apps.users.roles import sync_role_groups


def sync_roles_after_migrate(
    sender,
    app_config=None,
    using=DEFAULT_DB_ALIAS,
    apps=global_apps,
    **kwargs,
):
    # post_migrate fires once per installed app, after django.contrib.auth has
    # created that app's permissions, so each call grants only that app's
    # permissions. This covers apps listed after `users` in INSTALLED_APPS.
    if app_config is None:
        return

    try:
        group_model = apps.get_model("auth", "Group")
        apps.get_model("auth", "Permission")
    except LookupError:
        return

    if not router.allow_migrate_model(using, group_model):
        return

    sync_role_groups(app_label=app_config.label, using=using, apps=apps)
