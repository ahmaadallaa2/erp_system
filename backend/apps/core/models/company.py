from django.db import models
from django.db.models import Q # ضروري من أجل الـ Constraints
from django.utils.translation import gettext_lazy as _

from .base import SoftDeleteModel
from .sequences import Sequence

class Company(SoftDeleteModel):
    """
    موديل الشركة الأم.
    يمثل الكيان القانوني صاحب النظام.
    """
    name = models.CharField(_("اسم الشركة"), max_length=255)
    logo = models.ImageField(_("شعار الشركة"), upload_to='companies/logos/', null=True, blank=True)
    
    tax_number = models.CharField(_("الرقم الضريبي"), max_length=50, null=True, blank=True)
    commercial_record = models.CharField(_("السجل التجاري"), max_length=50, null=True, blank=True)
    
    email = models.EmailField(_("البريد الإلكتروني"), null=True, blank=True)
    phone = models.CharField(_("رقم الهاتف الرئيسي"), max_length=50, null=True, blank=True)
    website = models.URLField(_("الموقع الإلكتروني"), null=True, blank=True)
    address = models.TextField(_("العنوان الرئيسي"), null=True, blank=True)

    class Meta:
        verbose_name = _("الشركة")
        verbose_name_plural = _("الشركات")

    def __str__(self):
        return self.name

    

class Branch(SoftDeleteModel):
    # this is the company that the branch belongs to, required for multi-tenant architectures.
    # using a string reference 'core.Company' to prevent circular imports if they are in different files.
    company = models.ForeignKey(
        'core.Company', 
        on_delete=models.CASCADE, 
        related_name='branches',
        verbose_name=_("الشركة التابعة")
    )

    # the official name of the branch (e.g., "Main Cairo Branch")
    name = models.CharField(
        max_length=255, 
        verbose_name=_("اسم الفرع")
    )
    
    # a unique identifier for the branch, it can be auto-generated or manually entered.
    # unique=True is removed from the field level to allow soft-deleted branches to release their codes safely.
    code = models.CharField(
        max_length=50, 
        blank=True, # تم السماح بتركه فارغاً عشان دالة save تولده أوتوماتيك
        verbose_name=_("كود الفرع"), 
        help_text=_("يترك فارغاً للتوليد التلقائي (مثال: BR-001)")
    )
    
    # physical address of the branch, useful for geolocation, logistics, and reporting.
    address = models.TextField(
        null=True, 
        blank=True, 
        verbose_name=_("عنوان الفرع")
    )
    
    # primary contact number for the branch manager or reception.
    phone = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        verbose_name=_("هاتف الفرع")
    )
    
    # indicates if the branch is currently operating. Inactive branches won't appear in dropdowns for daily operations.
    is_active = models.BooleanField(
        default=True, 
        verbose_name=_("نشط")
    )

    # class meta to define string representations and strict database constraints.
    class Meta:
        verbose_name = _("فرع")
        verbose_name_plural = _("الفروع")
        ordering = ['company', 'name']
        
        # Smart constraint to ensure code uniqueness only among active (non-deleted) branches.
        # This prevents database IntegrityErrors if a deleted branch had the same code as a newly created one.
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'code'], 
                condition=Q(is_deleted=False), 
                name='unique_branch_code_per_company_active'
            )
            

        ]

    # this returns a readable format in the Django admin and foreign key dropdowns.
    def __str__(self):
        return f"[{self.code}] {self.name} - {self.company.name if self.company else ''}"

    # overriding the save method to auto-generate the branch code using our custom Sequence logic if left blank.
    def save(self, *args, **kwargs):
        if not self.code:
            # توليد الكود بناءً على الشركة التابع لها الفرع
            company_id = getattr(self, 'company_id', 1)
            seq_key = f"branch_code_comp_{company_id}"
            self.code = Sequence.next_number(seq_key, prefix='BR-', padding=3)
            
        super().save(*args, **kwargs)