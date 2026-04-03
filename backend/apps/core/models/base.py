import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType

from apps.core.models.audit import AuditLog
from apps.core.managers import SoftDeleteManager
from apps.core.middleware import get_current_user


class BaseModel(models.Model):
    # ====================
    # 1. الحقول (Fields)
    # ====================
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="تاريخ الإنشاء")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخر تعديل")

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
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

    # ====================
    # 2. الإعدادات (Meta)
    # ====================
    class Meta:
        abstract = True
        ordering = ['-created_at']

    # ====================
    # 3. دوال التهيئة والمساعدة (Init & Helpers)
    # ====================
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # الاحتفاظ بنسخة من القيم الأصلية عند تحميل الكائن من قاعدة البيانات
        self._original_state = self._get_current_state()

    def _get_current_state(self):
        # استخدمنا attname لنجلب الـ ID فقط (مثال: company_id) لمنع اللوب اللانهائي
        return {field.attname: getattr(self, field.attname) for field in self._meta.fields}

    def _log_audit(self, action, changes=None):
        user = get_current_user()

        AuditLog.objects.create(
            user=user if (user and user.is_authenticated) else None,
            action=action,
            content_type=ContentType.objects.get_for_model(self),
            object_id=str(self.pk),
            changes=changes or {}
        )

    def save(self, *args, **kwargs):
        user = get_current_user()
        is_new = self._state.adding

        if user and user.is_authenticated:
            if is_new or not self.created_by:
                self.created_by = user
            self.updated_by = user

        super().save(*args, **kwargs)

        changes = {}
        new_state = self._get_current_state()

        if is_new:
            action = AuditLog.ACTION_CREATE
            changes = {
                k: {'old': None, 'new': str(v)}
                for k, v in new_state.items()
                if v is not None
            }
        else:
            action = AuditLog.ACTION_UPDATE
            for field_name, old_value in self._original_state.items():
                new_value = new_state.get(field_name)
                # تجاهل حقول الوقت ومعرفات المستخدمين التقنية
                if old_value != new_value and field_name not in ['updated_at', 'updated_by_id', 'created_by_id']:
                    changes[field_name] = {
                        'old': str(old_value),
                        'new': str(new_value)
                    }

        if changes or is_new:
            self._log_audit(action=action, changes=changes)

        self._original_state = new_state


class SoftDeleteModel(BaseModel):
    """
    قالب الحذف الناعم (يرث من BaseModel):
    يضيف ميزة إخفاء السجلات بدلاً من حذفها نهائياً مع تتبع من قام بالحذف.
    """

    # ====================
    # 1. الحقول (Fields)
    # ====================
    is_deleted = models.BooleanField(default=False, db_index=True, verbose_name="محذوف؟")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="تاريخ الحذف")
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_deleted',
        verbose_name="حُذف بواسطة"
    )

    # ====================
    # 2. المدراء (Managers)
    # ====================
    objects = SoftDeleteManager()
    all_objects = models.Manager()

    # ====================
    # 3. الإعدادات (Meta)
    # ====================
    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        """
        هذه الدالة تخدع لوحة تحكم دجانغو (Admin):
        عندما يضغط المدير على "حذف"، دجانغو سينادي هذه الدالة،
        فنحن نوجهها لعمل حذف ناعم بدلاً من تدمير السجل نهائياً.
        """
        self.soft_delete()

    # ====================
    # 4. دوال الحذف والاسترجاع (Actions)
    # ====================
    def soft_delete(self):
        if self.is_deleted:
            return

        self.is_deleted = True
        self.deleted_at = timezone.now()

        user = get_current_user()
        if user and user.is_authenticated:
            self.deleted_by = user
            self.updated_by = user

        old_state = self._original_state.copy()

        # حفظ بدون المرور على BaseModel.save حتى لا يتسجل كـ update
        super(BaseModel, self).save(update_fields=[
            'is_deleted', 'deleted_at', 'deleted_by', 'updated_by', 'updated_at'
        ])

        self._log_audit(
            action=AuditLog.ACTION_DELETE,
            changes={
                'is_deleted': {'old': str(old_state.get('is_deleted')), 'new': str(self.is_deleted)},
                'deleted_at': {'old': str(old_state.get('deleted_at')), 'new': str(self.deleted_at)},
                'deleted_by_id': {'old': str(old_state.get('deleted_by_id')), 'new': str(self.deleted_by_id)},
            }
        )

        self._original_state = self._get_current_state()

    def restore(self):
        if not self.is_deleted:
            return

        old_state = self._original_state.copy()

        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None

        user = get_current_user()
        if user and user.is_authenticated:
            self.updated_by = user

        # حفظ بدون المرور على BaseModel.save حتى لا يتسجل كـ update
        super(BaseModel, self).save(update_fields=[
            'is_deleted', 'deleted_at', 'deleted_by', 'updated_by', 'updated_at'
        ])

        self._log_audit(
            action=AuditLog.ACTION_RESTORE,
            changes={
                'is_deleted': {'old': str(old_state.get('is_deleted')), 'new': str(self.is_deleted)},
                'deleted_at': {'old': str(old_state.get('deleted_at')), 'new': str(self.deleted_at)},
                'deleted_by_id': {'old': str(old_state.get('deleted_by_id')), 'new': str(self.deleted_by_id)},
            }
        )

        self._original_state = self._get_current_state()