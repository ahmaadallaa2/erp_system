from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.conf import settings

# لاحظ: هنا نرث من models.Model مباشرة وليس من BaseModel
class AuditLog(models.Model):
    """
    سجل التتبع (الصندوق الأسود).
    يخزن تفاصيل كل حركة تحدث في النظام.
    """
    
    # ====================
    # 1. ثوابت العمليات (Constants)
    # ====================
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    ACTION_RESTORE = 'restore'
    
    ACTION_CHOICES = (
        (ACTION_CREATE, _('إضافة')),
        (ACTION_UPDATE, _('تعديل')),
        (ACTION_DELETE, _('حذف')),
        (ACTION_RESTORE, _('استرجاع')),
    )

    # ====================
    # 2. الحقول الأساسية (Fields)
    # ====================
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("المستخدم")
    )

    action = models.CharField(_("نوع العملية"), max_length=15, choices=ACTION_CHOICES)
    
    # الربط الديناميكي مع أي جدول آخر
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50) # يستوعب الـ UUID والأرقام
    content_object = GenericForeignKey('content_type', 'object_id')

    changes = models.JSONField(_("التغييرات"), null=True, blank=True)
    
    timestamp = models.DateTimeField(_("وقت العملية"), auto_now_add=True)
    
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    browser_info = models.TextField(_("معلومات المتصفح"), null=True, blank=True)

    # ====================
    # 3. الإعدادات (Meta)
    # ====================
    class Meta:
        verbose_name = _("سجل تتبع")
        verbose_name_plural = _("سجلات التتبع")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=["content_type", "object_id", "-timestamp"]),
            models.Index(fields=["user"]),
            models.Index(fields=["action"]),
        ]

    # ====================
    # 4. الدوال (Methods)
    # ====================
    def __str__(self):
        return f"{self.user} - {self.action} - {self.content_type} ({self.timestamp})"

    # لا تضع دالة save هنا أبداً!