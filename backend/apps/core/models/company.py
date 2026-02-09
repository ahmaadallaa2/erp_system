from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import SoftDeleteModel  # وراثة من الموديل الأساسي

class Company(SoftDeleteModel):
    """
    موديل الشركة الأم.
    يمثل الكيان القانوني صاحب النظام.
    """
    # البيانات الأساسية
    name = models.CharField(_("اسم الشركة"), max_length=255)
    logo = models.ImageField(_("شعار الشركة"), upload_to='companies/logos/', null=True, blank=True)
    
    # البيانات القانونية (للفواتير)
    tax_number = models.CharField(_("الرقم الضريبي"), max_length=50, null=True, blank=True)
    commercial_record = models.CharField(_("السجل التجاري"), max_length=50, null=True, blank=True)
    
    # بيانات الاتصال
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
    # الربط بالشركة (One Company -> Many Branches)
    company = models.ForeignKey(
        Company, 
        on_delete=models.CASCADE, 
        related_name='branches',
        verbose_name=_("الشركة التابع لها")
    )

    name = models.CharField(_("اسم الفرع"), max_length=255)
    code = models.CharField(_("كود الفرع"), max_length=50, unique=True, help_text=_("مثال: BR-CAI-01"))
    
    # بيانات الاتصال الخاصة بالفرع
    address = models.TextField(_("عنوان الفرع"), null=True, blank=True)
    phone = models.CharField(_("هاتف الفرع"), max_length=50, null=True, blank=True)
    
    # هل الفرع نشط؟
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("فرع")
        verbose_name_plural = _("الفروع")
        ordering = ['company', 'name']

    def __str__(self):
        return f"{self.name} - {self.company.name}"