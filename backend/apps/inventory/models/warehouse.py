from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel, Branch
from apps.users.models import User

class Warehouse(SoftDeleteModel):
    """
    ملاحظة: هذا الكلاس يورث حقول (created_at, updated_at, created_by, updated_by)
    تلقائياً من SoftDeleteModel -> BaseModel.
    """
    name = models.CharField(_("اسم المخزن"), max_length=100)
    code = models.CharField(_("كود المخزن"), max_length=20, unique=True)
    
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='warehouses', 
        verbose_name=_("الفرع التابع له")
    )
    
    # ده حقل ممتاز ومختلف عن created_by
    # created_by: مين الموظف اللي قاعد عالكمبيوتر وسجل المخزن.
    # keeper: مين أمين المخزن المسئول عن العهدة (ممكن يكون شخص تاني).
    keeper = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='managed_warehouses',
        verbose_name=_("أمين المخزن")
    )
    
    address = models.CharField(_("العنوان التفصيلي"), max_length=255, blank=True)
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("مخزن")
        verbose_name_plural = _("المخازن")
        unique_together = ('name', 'branch')  # ممنوع تكرار اسم المخزن في نفس الفرع

    def __str__(self):
        return f"{self.name} ({self.branch.name})"