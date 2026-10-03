from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.users.roles import SYSTEM_ROLES, USER_TYPE_DEFAULT_ROLES, set_user_roles


class UserAdminService:
    @staticmethod
    @transaction.atomic
    def create_user(*, password, roles=None, **fields):
        user = get_user_model().objects.create_user(password=password, **fields)
        UserAdminService._sync_roles(user, roles or [], previous_user_type=None)
        return user

    @staticmethod
    @transaction.atomic
    def update_user(user, *, actor, password=None, roles=None, **fields):
        if user.pk == actor.pk and fields.get("is_active") is False:
            raise ValidationError({"is_active": "You cannot deactivate your own account."})

        previous_user_type = user.user_type
        for field, value in fields.items():
            setattr(user, field, value)
        if password:
            user.set_password(password)
        user.save()

        UserAdminService._sync_roles(user, roles, previous_user_type)
        return user

    @staticmethod
    def deactivate_user(user, *, actor):
        if user.pk == actor.pk:
            raise ValidationError("You cannot deactivate your own account.")
        user.soft_delete()
        return user

    @staticmethod
    def _sync_roles(user, roles, previous_user_type):
        """
        Explicit `roles` replace the user's ERP role groups. Without them the
        current roles are kept, minus the default role of a user_type the user
        no longer has. The default role of the current user_type is always added.
        """
        if roles is None:
            role_names = set(
                user.groups.filter(name__in=SYSTEM_ROLES).values_list("name", flat=True)
            )
            if previous_user_type != user.user_type:
                role_names.discard(USER_TYPE_DEFAULT_ROLES.get(previous_user_type))
        else:
            role_names = set(roles)

        default_role = USER_TYPE_DEFAULT_ROLES.get(user.user_type)
        if default_role:
            role_names.add(default_role)

        set_user_roles(user, role_names)
