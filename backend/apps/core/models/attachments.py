import os
import uuid
from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _
from apps.core.models.base import BaseModel

def get_attachment_upload_path(instance, filename):
    """
    دالة لتنظيم الملفات المرفوعة بأسماء آمنة للسحابة (Cloud-Safe).
    الشكل النهائي: attachments/product/uuid_of_product/random_uuid.pdf
    """
    model_name = instance.content_type.model
    object_id = instance.object_id
    
    # استخراج الامتداد الأصلي (مثل .pdf)
    ext = os.path.splitext(filename)[1].lower()
    
    # توليد اسم عشوائي آمن للملف الفعلي على السيرفر
    safe_filename = f"{uuid.uuid4().hex}{ext}"
    
    return f"attachments/{model_name}/{object_id}/{safe_filename}"


class Attachment(BaseModel):
    """
    موديل المرفقات العام.
    يسمح برفع ملفات (صور، PDF، Excel) وربطها بأي كائن في النظام.
    """
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=50) 
    content_object = GenericForeignKey('content_type', 'object_id')

    file = models.FileField(_("الملف"), upload_to=get_attachment_upload_path)
    name = models.CharField(_("اسم توضيحي"), max_length=255, blank=True)
    note = models.TextField(_("ملاحظات"), null=True, blank=True)
    
    file_type = models.CharField(_("نوع الامتداد"), max_length=10, blank=True)

    class Meta:
        verbose_name = _("مرفق")
        verbose_name_plural = _("المرفقات")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=["content_type", "object_id"]),
        ]

    def save(self, *args, **kwargs):
        # --- 1. معالجة الملفات القديمة عند التعديل ---
        if self.pk:
            try:
                old_instance = Attachment.objects.get(pk=self.pk)
                # لو تم رفع ملف جديد يختلف عن القديم، امسح القديم من السيرفر
                if old_instance.file and self.file and old_instance.file != self.file:
                    old_instance.file.delete(save=False)
            except Attachment.DoesNotExist:
                pass

        # --- 2. استخراج الامتداد والاسم بأمان ---
        if self.file:
            # جلب اسم الملف الفعلي بدون المسارات الطويلة
            original_filename = os.path.basename(self.file.name)
            
            # لو المستخدم مدخلش اسم توضيحي، نستخدم اسم الملف
            if not self.name:
                self.name = original_filename[:255] # قص الاسم لضمان عدم تخطي الـ max_length
                
            # استخراج الامتداد لتسهيل الفلترة
            ext = os.path.splitext(original_filename)[1][1:].lower()
            self.file_type = ext[:10] # ضمان عدم تخطي الـ max_length للامتداد

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name