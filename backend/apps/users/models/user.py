import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.users.managers import CustomUserManager
from apps.core.models.company import Company, Branch


class User(AbstractUser):
    """
    موديل المستخدم المخصص لنظام الـ ERP.
    يعتمد على البريد الإلكتروني (Email) بدلاً من اسم المستخدم،
    ويستخدم نظام دجانغو الافتراضي لتعطيل الحسابات (is_active) كبديل للحذف الناعم.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    username = None

    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    full_name = models.CharField(_("الاسم بالكامل"), max_length=255, blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    job_title = models.CharField(_("المسمى الوظيفي"), max_length=100, blank=True, null=True)

    USER_TYPE_CHOICES = (
        ('system_admin', 'مدير نظام (System Admin)'),
        ('company_admin', 'مدير شركة (Company Admin)'),
        ('branch_manager', 'مدير فرع (Branch Manager)'),
        ('employee', 'موظف (Employee)'),
    )
    user_type = models.CharField(
        _('نوع المستخدم'),
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='employee'
    )

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('الشركة')
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users',
        verbose_name=_('الفرع')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    objects = CustomUserManager()

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمين")
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.full_name or 'بدون اسم'} ({self.email})"

    def clean(self):
        super().clean()

        if self.branch and self.company and self.branch.company_id != self.company_id:
            raise ValidationError(_("الفرع المختار لا يتبع الشركة المحددة."))

        if self.branch and not self.company:
            self.company = self.branch.company

        if self.user_type == 'company_admin' and not self.company:
            raise ValidationError(_("مدير الشركة يجب أن يكون مرتبطًا بشركة."))

        if self.user_type == 'branch_manager' and (not self.company or not self.branch):
            raise ValidationError(_("مدير الفرع يجب أن يكون مرتبطًا بشركة وفرع."))

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def soft_delete(self):
        """
        عند رغبة المدير في حذف مستخدم، نقوم بتعطيله بدلاً من حذفه نهائياً.
        """
        self.is_active = False
        self.save(update_fields=['is_active'])