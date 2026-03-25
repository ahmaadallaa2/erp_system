# apps/accounting/models/journal.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel


class Journal(SoftDeleteModel):
    """
    نموذج دفاتر اليومية (Journals).
    يُستخدم لتقسيم القيود المحاسبية حسب نوع العملية (مبيعات، مشتريات، نقدية، إلخ).
    تسهل هذه الدفاتر عملية الفلترة واستخراج التقارير.
    """

    # =========================================================================
    # 1. الخيارات الثابتة والخرائط (Choices & Maps)
    # =========================================================================
    JOURNAL_TYPES = [
        ('sale',     _('مبيعات (Sales)')),
        ('purchase', _('مشتريات (Purchases)')),
        ('cash',     _('نقدية (Cash)')),
        ('bank',     _('بنك (Bank)')),
        ('general',  _('عمليات متنوعة (General/Miscellaneous)')),
    ]

    # خريطة الحماية: تحدد نوع الحساب المحاسبي المسموح به كـ "حساب افتراضي" لكل دفتر
    JOURNAL_ACCOUNT_TYPE_MAP = {
        'sale':     'income',  # المبيعات ترمي على حسابات الإيرادات
        'purchase': 'expense', # المشتريات ترمي على حسابات المصروفات/التكلفة
        'cash':     'asset',   # النقدية ترمي على حسابات الأصول (الخزينة)
        'bank':     'asset',   # البنوك ترمي على حسابات الأصول (حساب البنك)
        'general':  None,      # القيود العامة لا تتقيد بنوع معين
    }

    # =========================================================================
    # 2. حقول قاعدة البيانات (Database Fields)
    # =========================================================================
    name = models.CharField(
        max_length=100, 
        verbose_name=_("اسم الدفتر")
    )
    code = models.CharField(
        max_length=10, 
        unique=True, 
        verbose_name=_("الكود"),
        help_text=_("كود مختصر للدفتر، مثلاً: INV للمبيعات، BNK للبنك.")
    )
    type = models.CharField(
        max_length=20, 
        choices=JOURNAL_TYPES, 
        verbose_name=_("النوع")
    )

    # =========================================================================
    # 3. العلاقات (Relations)
    # =========================================================================
    default_account = models.ForeignKey(
        'accounting.Account', # استخدام String لتجنب الـ Circular Import
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name='default_journals',
        verbose_name=_("الحساب الافتراضي"),
        help_text=_(
            "يُستخدم هذا الحساب أوتوماتيكياً عند إنشاء قيد من هذا الدفتر. "
            "يجب أن يكون حساباً ختامياً (قابلاً للترحيل) ويتوافق مع نوع الدفتر."
        )
    )

    class Meta:
        verbose_name = _("دفتر يومية")
        verbose_name_plural = _("دفاتر اليومية")
        ordering = ['type', 'code'] # ترتيب منطقي في لوحة التحكم

    def __str__(self):
        return f"{self.name} ({self.code})"

    # =========================================================================
    # 4. قواعد التحقق (Validation Rules)
    # =========================================================================
    def clean(self):
        """
        ضمان سلامة إعدادات الدفتر قبل الحفظ في قاعدة البيانات.
        """
        if self.default_account:
            # 1. منع استخدام الحسابات التجميعية كحسابات افتراضية للدفتر
            # (نفس المنطق القوي اللي عملناه في شجرة الحسابات)
            if not self.default_account.is_leaf:
                raise ValidationError(
                    _('خطأ: الحساب الافتراضي يجب أن يكون حساباً ختامياً (قابلاً للترحيل)، '
                      'وليس حساباً تجميعياً.')
                )

            # 2. مطابقة نوع الحساب مع نوع الدفتر (Business Logic)
            expected_type = self.JOURNAL_ACCOUNT_TYPE_MAP.get(self.type)
            
            if expected_type and self.default_account.account_type != expected_type:
                # تم تعديل صياغة الرسالة هنا لتكون دقيقة ومفهومة للمحاسب
                raise ValidationError(
                    _(f'نوع الحساب غير متوافق! دفتر اليومية من نوع "{self.get_type_display()}" '
                      f'يتطلب حساباً افتراضياً من تصنيف مختلف، '
                      f'بينما الحساب الذي اخترته ("{self.default_account.name}") مصنف كـ "{self.default_account.get_account_type_display()}".')
                )