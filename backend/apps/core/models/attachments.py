import os
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from .base import BaseModel

def get_attachment_upload_path(instance, filename):
    """
    دالة لتنظيم الملفات المرفوعة.
    الشكل النهائي: attachments/Product/uuid/filename.pdf
    """
    # اسم الموديل (مثلاً: product)
    model_name = instance.content_type.model
    # الـ ID بتاع الأب
    object_id = instance.object_id
    # المسار
    return f"attachments/{model_name}/{object_id}/{filename}"

class Attachment(BaseModel):
    """
    موديل المرفقات العام.
    يسمح برفع ملفات (صور، PDF، Excel) وربطها بأي كائن في النظام.
    """
    # --- الربط العام (Generic Relation) ---
    # 1. نوع الموديل (فاتورة، منتج، يوزر)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    
    # 2. رقم الموديل (UUID)
    # خليناه CharField عشان يقبل UUID أو Integer لو ربطنا بحاجة تانية
    object_id = models.CharField(max_length=50)
    
    # 3. الرابط السحري اللي بيجمعهم
    content_object = GenericForeignKey('content_type', 'object_id')

    # --- بيانات الملف ---
    file = models.FileField(_("الملف"), upload_to=get_attachment_upload_path)
    name = models.CharField(_("اسم توضيحي"), max_length=255, blank=True)
    note = models.TextField(_("ملاحظات"), null=True, blank=True)
    
    # نوع الملف (للتسهيل في العرض)
    file_type = models.CharField(_("نوع الامتداد"), max_length=10, blank=True)

    class Meta:
        verbose_name = _("مرفق")
        verbose_name_plural = _("المرفقات")
        ordering = ['-created_at']
        # فهرس لسرعة البحث
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def save(self, *args, **kwargs):
        # استخراج الامتداد أوتوماتيكياً قبل الحفظ (مثلاً: pdf)
        if self.file:
            self.name = self.name or self.file.name
            ext = os.path.splitext(self.file.name)[1][1:].lower()
            self.file_type = ext
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name