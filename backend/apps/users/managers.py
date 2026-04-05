from django.contrib.auth.base_user import BaseUserManager
from django.utils.translation import gettext_lazy as _


class CustomUserManager(BaseUserManager):
    """
    مدير المستخدمين المخصص للنظام.
    يلغي الاعتماد على الـ username تماماً ويستخدم الـ email كمعرف أساسي،
    مع ضمان التشفير الصحيح لكلمات المرور.
    """

    def create_user(self, email, password=None, **extra_fields):
        """
        دالة لإنشاء مستخدم عادي وحفظه في قاعدة البيانات.
        """
        if not email:
            raise ValueError(_('يجب إدخال البريد الإلكتروني (Email)'))

        email = self.normalize_email(email)
        extra_fields.setdefault('is_active', True)

        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        دالة لإنشاء مدير النظام عند استخدام أمر:
        python manage.py createsuperuser
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('مدير النظام (Superuser) يجب أن يمتلك صلاحية is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('مدير النظام (Superuser) يجب أن يمتلك صلاحية is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)