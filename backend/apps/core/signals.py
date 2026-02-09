import json
from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.core.serializers.json import DjangoJSONEncoder
from .models import AuditLog, Attachment
from .middleware import get_current_user

# --- 1. مراقبة الحذف (عشان نمسح الملفات من السيرفر) ---
@receiver(post_delete, sender=Attachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    عند حذف سجل مرفق من الداتابيز، نقوم بحذف الملف الفعلي من السيرفر
    عشان المساحة متتمليش ملفات يتيمة.
    """
    if instance.file:
        instance.file.delete(False)

# --- 2. مراقبة التعديلات (Audit Log) ---
# لن نقوم بتفعيله على AuditLog نفسه عشان مندخلش في Loop لا نهائية
@receiver(post_save)
def log_save_changes(sender, instance, created, **kwargs):
    """
    تسجيل عمليات الإضافة والتعديل.
    """
    # تجاهل جداول الكور التقنية (عشان الزحمة)
    if sender in [AuditLog]: 
        return

    user = get_current_user()
    
    # تحديد نوع العملية
    action = AuditLog.ACTION_CREATE if created else AuditLog.ACTION_UPDATE
    
    # محاولة تسجيل اللوج (مغلفة بـ try عشان لو حصل خطأ ميعطلش السيستم)
    try:
        content_type = ContentType.objects.get_for_model(sender)
        
        # في حالة التعديل، ممكن مستقبلاً نضيف كود يقارن القيم القديمة بالجديدة
        changes = None 
        if not created:
            # هنا ممكن نضيف منطق معقد لمقارنة الحقول (Dirty Fields)
            pass

        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=content_type,
            object_id=str(instance.pk),
            changes=changes
        )
    except Exception as e:
        # لو فشل التسجيل، اطبع الخطأ في الكونسول بس متوقفش السيستم
        print(f"Audit Log Error: {e}")

@receiver(post_delete)
def log_delete_changes(sender, instance, **kwargs):
    """
    تسجيل عمليات الحذف.
    """
    if sender in [AuditLog]:
        return

    user = get_current_user()
    try:
        content_type = ContentType.objects.get_for_model(sender)
        AuditLog.objects.create(
            user=user,
            action=AuditLog.ACTION_DELETE,
            content_type=content_type,
            object_id=str(instance.pk),
            changes={"note": "Record deleted"}
        )
    except Exception as e:
        print(f"Audit Log Delete Error: {e}")