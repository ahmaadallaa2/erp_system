# apps/sales/models/invoice.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from decimal import Decimal
from apps.core.models import SoftDeleteModel, Sequence

class SalesInvoice(SoftDeleteModel):
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('confirmed', _('مؤكدة / تم التسليم')),
        ('cancelled', _('ملغاة')),
    ]

    PAYMENT_CHOICES = [
        ('credit', 'آجل (على الحساب)'),
        ('cash', 'كاش (نقدي)'),
    ]

    invoice_number = models.CharField(_("رقم الفاتورة"), max_length=50, unique=True, blank=True)
    
    # هنا بنربط بالعميل (Partner)
   # ... جوه كلاس SalesInvoice ...
    
    customer = models.ForeignKey(
        'partners.Partner', 
        on_delete=models.RESTRICT, 
        related_name='sales_invoices',
        verbose_name=_("العميل"),
        limit_choices_to={'partner_type__in': ['customer', 'both']}
    )
    
    # الحقل الجديد اللي هنضيفه
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='sales_invoices',
        verbose_name=_("المخزن (يُصرف منه)"),
        null=True, # حطيناها True مؤقتاً عشان المايجريشن ميضربش لو عندك فواتير قديمة متسجلة
    )

    payment_type = models.CharField(_("طريقة الدفع"), max_length=10, choices=PAYMENT_CHOICES, blank=True)

    treasury_account = models.ForeignKey(
        'accounting.Account', 
        on_delete=models.RESTRICT, 
        related_name='cash_sales',
        verbose_name=_("حساب الخزينة (للكاش)"),
        null=True, blank=True,
        limit_choices_to={'code__startswith': '1001'} # بافتراض إن كود الخزينة عندك بيبدأ بـ 1001

    )
    date = models.DateField(_("تاريخ الفاتورة"), default=timezone.now)
    status = models.CharField(_("الحالة"), max_length=20, choices=STATUS_CHOICES, default='draft')
    
    notes = models.TextField(_("ملاحظات"), blank=True)

    class Meta:
        verbose_name = _("فاتورة مبيعات")
        verbose_name_plural = _("فواتير المبيعات")
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.name}"

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # استخدام التسلسل التلقائي اللي برمجناه في الكور
            self.invoice_number = Sequence.next_number('sales_invoice_sequence', prefix='INV-', padding=5)
        super().save(*args, **kwargs)

    @property
    def total_amount(self):
        # لو مفيش id (يعني الفاتورة لسه بتتكريت ومفيهاش منتجات)، رجع صفر
        if not self.pk:
            return Decimal('0.00')
        
        # تجميع إجمالي الفاتورة من السطور
        total = sum(item.total_price for item in self.items.all())
        return total or Decimal('0.00')


class SalesInvoiceItem(models.Model):
    invoice = models.ForeignKey(
        SalesInvoice, 
        on_delete=models.CASCADE, 
        related_name='items',
        verbose_name=_("الفاتورة")
    )
    product = models.ForeignKey(
        'inventory.Product', 
        on_delete=models.RESTRICT, 
        related_name='sales_items',
        verbose_name=_("المنتج")
    )
    
    quantity = models.DecimalField(_("الكمية"), max_digits=10, decimal_places=2, default=Decimal('1.00')) 
    # (تأكد إنك عامل from decimal import Decimal فوق)
    unit_price = models.DecimalField(_("سعر الوحدة"), max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = _("صنف الفاتورة")
        verbose_name_plural = _("أصناف الفاتورة")

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"

    @property
    def total_price(self):
        # بنحول الكمية والسعر لـ String وبعدين Decimal عشان نمنع أي كراش
        qty = Decimal(str(self.quantity or '0'))
        price = Decimal(str(self.unit_price or '0'))
        return qty * price