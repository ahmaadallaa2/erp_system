import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from apps.core.managers import SoftDeleteManager
from apps.core.middleware import get_current_user 

class BaseModel(models.Model):
    """
    القالب الأساسي الشامل:
    1. UUID (Primary Key)
    2. Timestamps (Created/Updated At)
    3. Userstamps (Created/Updated By)
    """
    # --- المعرف ---
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # --- التوقيتات ---
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تعديل")

    # --- التتبع (مين عمل إيه) ---
    # بنستخدم settings.AUTH_USER_MODEL عشان نتجنب مشاكل التداخل (Circular Import)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # لو اليوزر اتمسح، السجل يفضل موجود بس الحقل فاضي
        null=True, 
        blank=True, 
        related_name='%(class)s_created', # اسم فريد للعلاقة العكسية
        verbose_name="أنشئ بواسطة"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='%(class)s_updated',
        verbose_name="عُدل بواسطة"
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """
        تعديل دالة الحفظ عشان تلقط اليوزر أوتوماتيك
        """
        user = get_current_user()
        
        # لو اليوزر موجود ومسجل دخول (مش Anonymous)
        if user and user.is_authenticated:
            # لو ده إنشاء جديد (مفيش ID لسه أو created_by فاضي)
            if not self.pk or not self.created_by:
                self.created_by = user
            
            # دايماً حدث الـ updated_by
            self.updated_by = user

        super().save(*args, **kwargs)


class SoftDeleteModel(BaseModel):
    """
    قالب الحذف الناعم (يرث كل ما سبق ويضيف الحذف)
    """
    is_deleted = models.BooleanField(default=False, verbose_name="محذوف؟")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        # هنا كمان هنسجل مين اللي حذف لو الميدلوير شغال
        user = get_current_user()
        if user and user.is_authenticated:
            self.updated_by = user
            
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save()

    class Meta:
        abstract = True