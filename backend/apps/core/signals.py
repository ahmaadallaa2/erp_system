from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Attachment

# --- مراقبة الحذف (لتنظيف مساحة السيرفر) ---
@receiver(post_delete, sender=Attachment)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    عند حذف سجل مرفق من الداتابيز، نقوم بحذف الملف الفعلي من السيرفر
    لعدم إهدار مساحة التخزين.
    """
    if instance.file:
        instance.file.delete(False)