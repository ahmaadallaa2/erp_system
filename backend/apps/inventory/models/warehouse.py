# apps/inventory/models/warehouse.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel, Branch, Sequence 
from apps.users.models import User

class Warehouse(SoftDeleteModel):
    
    # --- الإضافة الجديدة: أنواع المخازن ---
    WAREHOUSE_TYPES = [
        ('main', _('مخزن رئيسي (Main)')),
        ('sub',  _('مخزن فرعي / معرض (Showroom)')),
    ]

    name = models.CharField(_("اسم المخزن"), max_length=100)
    
    # ضفنا blank=True عشان الفورم متطلبوش اجباري، والسيستم هو اللي هيكتبه في الـ save
    code = models.CharField(_("كود المخزن"), max_length=20, unique=True, blank=True)
    
    # الإضافة الجوهرية للوجيك الحركات
    warehouse_type = models.CharField(
        _("نوع المخزن"), 
        max_length=20, 
        choices=WAREHOUSE_TYPES, 
        default='sub'
    )
    
    branch = models.ForeignKey(
        Branch, 
        on_delete=models.CASCADE, 
        related_name='warehouses', 
        verbose_name=_("الفرع التابع له")
    )
    
    # keeper: مين أمين المخزن المسئول عن العهدة.
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
        # تعديل بسيط لعرض نوع المخزن جنب اسمه
        return f"{self.name} - {self.get_warehouse_type_display()} ({self.branch.name})"

    def save(self, *args, **kwargs):
        # توليد التسلسل التلقائي لكود المخزن
        if not self.code:
            # لو المخزن بيورث company_id من BaseModel تقدر تستخدم self.company_id
            # لو لأ، ممكن نعتمد على id الفرع أو شركة الفرع (self.branch.company_id)
            company_id = getattr(self, 'company_id', getattr(self.branch, 'company_id', self.branch_id))
            
            seq_key = f"warehouse_code_comp_{company_id}"
            
            # بادئة WH- تعبر عن Warehouse، و padding=4 عشان يكون مثلاً WH-0001
            self.code = Sequence.next_number(seq_key, prefix='WH-', padding=4)
            
        super().save(*args, **kwargs)