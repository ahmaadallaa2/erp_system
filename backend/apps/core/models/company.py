from django.db import models
from django.db.models import Q # ضروري من أجل الـ Constraints
from django.utils.translation import gettext_lazy as _
from .base import SoftDeleteModel  

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
    """
    موديل الفروع.
    كل فرع يتبع شركة واحدة، ويستخدم لربط الموظفين والمخازن والمبيعات بمكان محدد.
    """
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, # يظل مفيداً في حالة الـ Hard Delete من الداتابيز مباشرة
        related_name='branches',
        verbose_name=_("الشركة التابع لها")
    )

    name = models.CharField(_("اسم الفرع"), max_length=255)
    # قمنا بإزالة unique=True من هنا
    code = models.CharField(_("كود الفرع"), max_length=50, help_text=_("مثال: BR-CAI-01"))
    
    address = models.TextField(_("عنوان الفرع"), null=True, blank=True)
    phone = models.CharField(_("هاتف الفرع"), max_length=50, null=True, blank=True)
    
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("فرع")
        verbose_name_plural = _("الفروع")
        ordering = ['company', 'name']
        
        # حل الفخ الأول: القيود الذكية
        constraints = [
            models.UniqueConstraint(
                fields=['code'],
                condition=Q(is_deleted=False), # لا تسمح بتكرار الكود فقط إذا كان الفرع غير محذوف
                name='unique_active_branch_code'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"