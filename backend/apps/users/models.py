from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel

class User(AbstractUser, SoftDeleteModel):
    """
    موديل المستخدم:
    يعتمد على Username (الافتراضي) + Email + خصائص الـ ERP.
    """
    # 1. رجعنا اليوزر نيم (لأننا ورثنا من AbstractUser ومكتبناش username = None)
    
    # تأكد إن الإيميل فريد (مهم عشان ميكونش فيه تكرار)
    email = models.EmailField(_('email address'), unique=True)
    
    # حقول إضافية
    full_name = models.CharField(_("الاسم بالكامل"), max_length=255, blank=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    job_title = models.CharField(_("المسمى الوظيفي"), max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = _("مستخدم")
        verbose_name_plural = _("المستخدمين")
        ordering = ['-created_at']

    def __str__(self):
        # عرض اليوزر نيم (وبين قوسين الاسم الحقيقي لو موجود)
        return f"{self.username} ({self.full_name or 'No Name'})"