from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel, Sequence

class Partner(SoftDeleteModel):
    class PartnerType(models.TextChoices):
        CUSTOMER = 'customer', _('عميل')
        SUPPLIER = 'supplier', _('مورد')
        BOTH = 'both', _('عميل ومورد')

    class EntityType(models.TextChoices):
        INDIVIDUAL = 'individual', _('فرد')
        COMPANY = 'company', _('شركة')

    # 1. البيانات الأساسية
    name = models.CharField(_("الاسم التجاري / الكامل"), max_length=150)
    code = models.CharField(_("كود الجهة"), max_length=50, unique=True, blank=True)
    
    partner_type = models.CharField(_("النوع"), max_length=20, choices=PartnerType.choices, default=PartnerType.CUSTOMER)
    entity_type = models.CharField(_("نوع الكيان"), max_length=20, choices=EntityType.choices, default=EntityType.COMPANY)
    
    # 2. بيانات التواصل
    phone = models.CharField(_("رقم الهاتف"), max_length=20)
    email = models.EmailField(_("البريد الإلكتروني"), blank=True, null=True)
    address = models.TextField(_("العنوان التفصيلي"), blank=True)
    
    # 3. البيانات القانونية (مهمة جداً لفواتير المبيعات والمشتريات)
    tax_number = models.CharField(_("الرقم الضريبي (VAT)"), max_length=50, blank=True, null=True)
    commercial_record = models.CharField(_("السجل التجاري"), max_length=50, blank=True, null=True)
    
    is_active = models.BooleanField(_("نشط"), default=True)

    class Meta:
        verbose_name = _("شريك (عميل/مورد)")
        verbose_name_plural = _("جهات التعامل")
        ordering = ['name']

    def __str__(self):
        return f"[{self.code}] {self.name} - {self.get_partner_type_display()}"

    def save(self, *args, **kwargs):
        # توليد الكود التلقائي بناءً على نوع جهة التعامل
        if not self.code:
            company_id = getattr(self, 'company_id', 1) 
            
            # تحديد البادئة ومفتاح التسلسل بناءً على النوع
            if self.partner_type == self.PartnerType.CUSTOMER:
                prefix = 'CUST-'
                seq_key = f"customer_code_comp_{company_id}"
                
            elif self.partner_type == self.PartnerType.SUPPLIER:
                prefix = 'SUP-'
                seq_key = f"supplier_code_comp_{company_id}"
                
            else: 
                # حالة (عميل ومورد معاً - BOTH)
                prefix = 'PRT-'
                seq_key = f"partner_code_both_comp_{company_id}"
                
            # توليد الرقم النهائي
            self.code = Sequence.next_number(seq_key, prefix=prefix, padding=5)
            
        super().save(*args, **kwargs)