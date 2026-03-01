from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from apps.core.models import SoftDeleteModel, Sequence
from apps.partners.models import Partner


class PurchaseOrder(SoftDeleteModel):
    #this is the status of the order, it can be draft, sent, approved, cancelled, or converted to invoice
    STATUS_CHOICES = [
        ('draft', _('مسودة')),
        ('sent', _('تم الإرسال')),
        ('approved', _('موافق عليه')),
        ('cancelled', _('ملغي')),
        ('converted', _('تحول لفاتورة')),
    ]

    #this is the purchase order number, it is generated automatically based on the sequence defined in the settings, but it can be edited by the user if needed
    po_number = models.CharField(
        max_length=50, 
        unique=True, 
        blank=True, 
        null=True, 
        verbose_name=_("رقم أمر الشراء")
    )

    #this is the branch that the purchase order belongs to, it is required and it is used to filter the purchase orders by branch in the views and reports
    branch = models.ForeignKey(
        'core.Branch', 
        on_delete=models.CASCADE, 
        related_name='purchase_orders', 
        verbose_name=_("الفرع")
    )

    #this is the supplier that the purchase order is related to, it is required and it is used to filter the purchase orders by supplier in the views and reports
    supplier = models.ForeignKey(
        Partner, 
        on_delete=models.RESTRICT, 
        limit_choices_to={'partner_type__in': ['supplier', 'both']},
        related_name='purchase_orders', 
        verbose_name=_("المورد")
    )

    #this is the warehouse that the purchase order is related to, it is required and it is used to filter the purchase orders by warehouse in the views and reports
    warehouse = models.ForeignKey(
        'inventory.Warehouse',
        on_delete=models.RESTRICT,
        related_name='purchase_orders',
        verbose_name=_("مخزن الاستلام")
    )

    #this is the status of the purchase order, it is used to track the progress of the purchase order and to filter the purchase orders by status in the views and reports
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='draft', 
        verbose_name=_("الحالة")
    )

    #this is the date of the purchase order, it is used to track the date of the purchase order and to filter the purchase orders by date in the views and reports
    order_date = models.DateField(
        default=timezone.now,
        verbose_name=_("تاريخ الطلب")
    )
    #this is the expected delivery date of the purchase order, it is used to track the expected delivery date of the purchase order and to filter the purchase orders by expected delivery date in the views and reports
    delivery_date = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("تاريخ التوريد المتوقع")
    )

    #this is the total amount of the purchase order, it is calculated based on the purchase order lines and it is used to track the total amount of the purchase order and to filter the purchase orders by total amount in the views and reports
    total_amount = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0.00, 
        verbose_name=_("إجمالي أمر الشراء"),
        editable=False # عشان الإجمالي هيتحسب أوتوماتيك من المنتجات ومش هيتعدل يدوي
    )

    #this is the notes of the purchase order, it is used to add any additional information about the purchase order and it is optional
    notes = models.TextField(blank=True, verbose_name=_("ملاحظات"))

    #this is the class meta of the purchase order model, it is used to define the verbose name and the ordering of the purchase orders in the views and reports
    class Meta:
        verbose_name = _("أمر شراء")
        verbose_name_plural = _("أوامر الشراء")
        ordering = ['-order_date', '-id']

    #this is the def str__ method of the purchase order model, it is used to return a string representation of the purchase order that includes the purchase order number and the supplier name (if available) for easy identification in the admin and other views
    def __str__(self):
        return f"[{self.po_number}] {self.supplier.name if self.supplier else 'بدون مورد'}"
    
    #this is the save method of the purchase order model, it is used to generate the purchase order number automatically based on the sequence defined in the settings when the purchase order is created for the first time, and to calculate the total amount of the purchase order based on the purchase order lines when the purchase order is saved
    def save(self, *args, **kwargs):
        # توليد رقم أمر الشراء أوتوماتيك باستخدام Sequence الكور
        if not self.po_number:
            # ربط السيريال بالفرع عشان كل فرع يكون ليه تسلسل مستقل (اختياري بس احترافي)
            branch_id = getattr(self, 'branch_id', 1) 
            seq_key = f"po_branch_{branch_id}"
            
            # لو حابب تخليه عام لكل الشركة، ممكن تشيل الفرع من المفتاح
            self.po_number = Sequence.next_number(seq_key, prefix='PO-', padding=5)
            
        super().save(*args, **kwargs)
