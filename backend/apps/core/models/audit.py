from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from django.conf import settings

class AuditLog(models.Model):
    """
    سجل التتبع (الصندوق الأسود).
    يخزن تفاصيل كل حركة تحدث في النظام.
    """
    ACTION_CREATE = 'create'
    ACTION_UPDATE = 'update'
    ACTION_DELETE = 'delete'
    
    ACTION_CHOICES = (
        (ACTION_CREATE, _('إضافة')),
        (ACTION_UPDATE, _('تعديل')),
        (ACTION_DELETE, _('حذف')),
    )

    # 1. من قام بالفعل؟
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("المستخدم")
    )

    # 2. ماذا فعل؟
    action = models.CharField(_("نوع العملية"), max_length=10, choices=ACTION_CHOICES)
    
    # 3. على أي جدول وأي سجل؟ (Generic Relation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50) # UUID as string
    content_object = GenericForeignKey('content_type', 'object_id')

    # 4. تفاصيل التغيير (JSON)
    # الشكل: {"price": {"old": 100, "new": 200}, "status": {"old": "draft", "new": "confirmed"}}
    changes = models.JSONField(_("التغييرات"), null=True, blank=True)
    
    # 5. متى؟
    timestamp = models.DateTimeField(_("وقت العملية"), auto_now_add=True)
    
    # 6. معلومات إضافية (اختياري)
    ip_address = models.GenericIPAddressField(_("IP Address"), null=True, blank=True)
    browser_info = models.CharField(_("معلومات المتصفح"), max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = _("سجل تتبع")
        verbose_name_plural = _("سجلات التتبع")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.content_type} ({self.timestamp})"