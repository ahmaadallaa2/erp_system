import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from apps.users.managers import CustomUserManager
from apps.core.models.company import Company, Branch

class User(AbstractUser):
    """
    موديل المستخدم المخصص لنظام الـ ERP.
    يعتمد على البريد الإلكتروني (Email) بدلاً من اسم المستخدم،
    ويستخدم نظام دجانغو الافتراضي لتعطيل الحسابات (is_active) كبديل للحذف الناعم.
    """
    # 1. المعرف (ID) الآمن
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # 2. إزالة حقل username الافتراضي تماماً لتجنب التكرار
    username = None 

    # 3. الحقول الأساسية
    email = models.EmailField(_('البريد الإلكتروني'), unique=True)
    full_name = models.CharField(_("الاسم بالكامل"), max_length=255, blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    job_title = models.CharField(_("المسمى الوظيفي"), max_length=100, blank=True, null=True)

    # 4. الربط بصلاحيات الشركة (Multi-tenancy)
    USER_TYPE_CHOICES = (
        ('system_admin', 'مدير نظام (System Admin)'),
        ('company_admin', 'مدير شركة (Company Admin)'),
        ('branch_manager', 'مدير فرع (Branch Manager)'),
        ('employee', 'موظف (Employee)'),
    )
    user_type = models.CharField(_('نوع المستخدم'), max_length=20, choices=USER_TYPE_CHOICES, default='employee')
    
    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, null=True, blank=True, 
        related_name='users', verbose_name=_('الشركة')
    )
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, blank=True, 
        related_name='users', verbose_name=_('الفرع')
    )

    # 5. إعدادات دجانغو لمدير التسجيل
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name'] # الحقول المطلوبة عند إنشاء superuser

    # ربط الموديل بالـ Manager الذي كتبناه سابقاً
    objects = CustomUserManager()

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمين")
        ordering = ['-date_joined'] # استخدمنا حقل دجانغو الافتراضي بدلاً من created_at

    def __str__(self):
        return f"{self.full_name or 'بدون اسم'} ({self.email})"

    # 💡 بديل الحذف الناعم (Soft Delete) المتوافق مع دجانغو
    def soft_delete(self):
        """
        عند رغبة المدير في حذف مستخدم، نقوم بتعطيله بدلاً من حذفه نهائياً
        """
        self.is_active = False
        self.save(update_fields=['is_active'])