from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import SoftDeleteModel, Sequence
from django.conf import settings

class Partner(SoftDeleteModel):
    # استخدام TextChoices هو الأسلوب الأحدث والأكثر تنظيماً في Django
    class PartnerType(models.TextChoices):
        CUSTOMER = 'customer', _('عميل')
        SUPPLIER = 'supplier', _('مورد')
        BOTH = 'both', _('عميل ومورد')

    code = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True,
        verbose_name=_("كود العميل/المورد"),
        help_text=_("يترك فارغاً للتوليد التلقائي")
    )
    
    partner_type = models.CharField(
        max_length=20, 
        choices=PartnerType.choices, 
        default=PartnerType.CUSTOMER, 
        verbose_name=_("النوع")
    )
    
    name = models.CharField(max_length=150, verbose_name=_("الاسم التجاري / الكامل"))
    
    phone = models.CharField(max_length=20, verbose_name=_("رقم الهاتف"))
    mobile = models.CharField(max_length=20, blank=True, null=True, verbose_name=_("رقم الجوال (إضافي)"))
    email = models.EmailField(blank=True, null=True, verbose_name=_("البريد الإلكتروني"))
    website = models.URLField(blank=True, null=True, verbose_name=_("الموقع الإلكتروني"))
    
    address = models.TextField(blank=True, verbose_name=_("العنوان التفصيلي"))
    city = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("المدينة"))
    tax_number = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("الرقم الضريبي (VAT)"))
    commercial_record = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("السجل التجاري"))
    
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("حد الائتمان"))
    
    # الرصيد الافتتاحي (يُضبط مرة واحدة عند الإنشاء)
    initial_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name=_("الرصيد الافتتاحي"))
    
    # الرصيد الحالي (يتم تحديثه تلقائياً ولا يعدل يدوياً)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=0, verbose_name=_("الرصيد الحالي"), editable=False)

    is_active = models.BooleanField(default=True, verbose_name=_("نشط"))
    notes = models.TextField(blank=True, null=True, verbose_name=_("ملاحظات داخلية"))
    
    responsible = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='partners',
        verbose_name=_("الموظف المسؤول")
    )

    class Meta:
        verbose_name = _("شريك (عام)")
        verbose_name_plural = _("الشركاء")
        ordering = ['name']

    def __str__(self):
        return f"[{self.code}] {self.name} - {self.get_partner_type_display()}"
    
    def save(self, *args, **kwargs):
        # 1. ضبط الرصيد الافتتاحي عند الإنشاء لأول مرة فقط
        if not self.pk and not self.balance:
            self.balance = self.initial_balance
            
        # 2. توليد الكود التلقائي (مستقل لضمان التوليد في كل الحالات لو الحقل فارغ)
        if not self.code:
            company_id = getattr(self, 'company_id', 1) 
            
            if self.partner_type == self.PartnerType.CUSTOMER:
                prefix = 'CUST-'
                seq_key = f"customer_code_comp_{company_id}"
            elif self.partner_type == self.PartnerType.SUPPLIER:
                prefix = 'SUP-'
                seq_key = f"supplier_code_comp_{company_id}"
            else: 
                prefix = 'PRT-'
                seq_key = f"partner_code_both_comp_{company_id}"
                
            self.code = Sequence.next_number(seq_key, prefix=prefix, padding=5)
                
        # استدعاء دالة الحفظ الأساسية
        super().save(*args, **kwargs)