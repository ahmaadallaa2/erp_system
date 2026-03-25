# apps/accounting/models/entry.py

from decimal import Decimal
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from apps.core.models import SoftDeleteModel, Sequence


class JournalEntry(SoftDeleteModel):
    """
    نموذج قيد اليومية (Journal Entry).
    يمثل المعاملة المالية الكاملة (رأس القيد) التي تتكون من عدة سطور (مدين ودائن).
    """

    # =========================================================================
    # 1. الخيارات الثابتة (Choices)
    # =========================================================================
    STATUS_CHOICES = [
        ('draft',     _('مسودة (Draft)')),
        ('posted',    _('مُرحّل (Posted)')),
        ('cancelled', _('ملغي (Cancelled)')),
    ]

    # =========================================================================
    # 2. العلاقات والبيانات الأساسية (Relations & Core Data)
    # =========================================================================
    journal = models.ForeignKey(
        'accounting.Journal',
        on_delete=models.RESTRICT,
        related_name='entries',
        verbose_name=_("دفتر اليومية")
    )
    entry_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name=_("رقم القيد"),
        help_text=_("يتم توليده تلقائياً عند الحفظ بناءً على كود الدفتر.")
    )
    date = models.DateField(
        default=timezone.now,
        verbose_name=_("تاريخ القيد")
    )
    reference = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("رقم المرجع (رقم الفاتورة/السند)"),
        help_text=_("يُستخدم لربط القيد بالمستند الأصلي (مثال: INV-2026-001).")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_("الحالة")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("البيان / الملاحظات")
    )

    class Meta:
        verbose_name = _("قيد يومية")
        verbose_name_plural = _("قيود اليومية")
        ordering = ['-date', '-id']  # الأحدث يظهر أولاً

    def __str__(self):
        return f"{self.entry_number} - {self.reference or 'بدون مرجع'}"

    # =========================================================================
    # 3. قواعد التحقق (Validation Rules)
    # =========================================================================
    def clean(self):
        """
        التحقق من سلامة القيد قبل حفظه في قاعدة البيانات.
        """
        # 1. حماية القيود المُرحلة والملغاة من أي تعديل في البيانات
        #    نسمح فقط بتغيير الـ status — أي تعديل آخر مرفوض
        if self.pk:
            original = (
                JournalEntry.objects
                .filter(pk=self.pk)
                .values_list('status', flat=True)
                .first()
            )
            if original and original in ('posted', 'cancelled'):
                # لو الـ status لم يتغير، معناه حد بيعدل بيانات تانية → مرفوض
                if self.status == original:
                    raise ValidationError(
                        _('لا يمكن تعديل بيانات قيد مُرحّل أو ملغي. '
                          'يجب إنشاء قيد عكسي لتصحيحه.')
                    )

        # 2. ضمان التوازن الإجباري عند الترحيل
        #    يحمي النظام لو تم تغيير الحالة مباشرة من لوحة تحكم Django
        if self.status == 'posted':
            self.validate_balanced()

    def validate_balanced(self):
        """
        يتحقق من توازن القيد (إجمالي المدين = إجمالي الدائن).
        يُستدعى إجبارياً قبل الترحيل.
        """
        # التأكد من وجود سطور للقيد أولاً
        if not self.pk or not self.items.exists():
            raise ValidationError(
                _('لا يمكن ترحيل قيد فارغ لا يحتوي على أسطر محاسبية.')
            )

        # حساب المجاميع من قاعدة البيانات مباشرة (Performance Optimized)
        totals = self.items.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit')
        )
        total_debit  = totals.get('total_debit')  or Decimal('0.00')
        total_credit = totals.get('total_credit') or Decimal('0.00')

        # شرط التوازن المحاسبي
        if total_debit != total_credit:
            raise ValidationError(
                _(f'القيد غير متوازن: '
                  f'إجمالي المدين ({total_debit}) '
                  f'لا يساوي إجمالي الدائن ({total_credit}).')
            )

        # منع ترحيل القيود الصفرية
        if total_debit == Decimal('0.00'):
            raise ValidationError(_('لا يمكن ترحيل قيد بقيمة صفر.'))

    # =========================================================================
    # 4. العمليات المحاسبية (Accounting Actions)
    # =========================================================================
    def post(self):
        """ترقية القيد من مسودة إلى مُرحّل بعد التحقق من توازنه."""
        if self.status != 'draft':
            raise ValidationError(_('يمكن ترحيل المسودات فقط.'))

        self.status = 'posted'
        self.clean()  # يستدعي validate_balanced() تلقائياً
        self.save(update_fields=['status'])

    def cancel(self):
        """
        إلغاء القيد.
        القيود الملغاة تبقى في قاعدة البيانات لأغراض المراجعة (Audit Trail).
        """
        if self.status == 'cancelled':
            raise ValidationError(_('القيد ملغي بالفعل.'))
        if self.status == 'posted':
            raise ValidationError(
                _('لا يمكن إلغاء قيد مُرحّل مباشرةً. '
                  'يجب إنشاء قيد عكسي أولاً للحفاظ على التسلسل المالي.')
            )

        self.status = 'cancelled'
        self.save(update_fields=['status'])

    # =========================================================================
    # 5. الحفظ (Save)
    # =========================================================================
    def save(self, *args, **kwargs):
        """
        توليد رقم القيد التسلسلي أوتوماتيكياً قبل الحفظ الأول.
        مثال: دفتر كوده INV → الرقم هيكون INV-0001
        """
        if not self.entry_number:
            seq_key = f"journal_{self.journal.code}"
            self.entry_number = Sequence.next_number(
                seq_key,
                prefix=f"{self.journal.code}-",
                padding=4
            )
        super().save(*args, **kwargs)


# =============================================================================
# =============================================================================


class JournalItem(SoftDeleteModel):
    """
    نموذج سطر القيد (Journal Item).
    يمثل طرفاً واحداً من المعاملة المالية (إما مدين أو دائن).
    """

    # =========================================================================
    # 1. العلاقات والبيانات (Relations & Data)
    # =========================================================================
    entry = models.ForeignKey(
        JournalEntry,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_("قيد اليومية")
    )
    account = models.ForeignKey(
        'accounting.Account',
        on_delete=models.RESTRICT,
        related_name='journal_items',
        verbose_name=_("الحساب")
    )
    partner = models.ForeignKey(
        'partners.Partner',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journal_items',
        verbose_name=_("الشريك (مورد / عميل)"),
        help_text=_("إلزامي للحسابات التي تقبل التسوية (كالعملاء والموردين).")
    )
    description = models.CharField(
        max_length=255,
        verbose_name=_("البيان")
    )

    # =========================================================================
    # 2. المبالغ (Amounts)
    # =========================================================================
    debit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("مدين (Debit)")
    )
    credit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00,
        verbose_name=_("دائن (Credit)")
    )

    class Meta:
        verbose_name = _("سطر القيد")
        verbose_name_plural = _("سطور القيد")

    def __str__(self):
        return f"{self.account.name} - مدين: {self.debit} | دائن: {self.credit}"

    # =========================================================================
    # 3. قواعد التحقق (Validation Rules)
    # =========================================================================
    def clean(self):
        """
        التحقق من سلامة السطر المحاسبي.
        """
        # 0. حماية أمنية: منع تعديل سطور قيد مُرحّل أو ملغي
        if self.entry_id:
            entry_status = (
                JournalEntry.objects
                .filter(pk=self.entry_id)
                .values_list('status', flat=True)
                .first()
            )
            if entry_status in ('posted', 'cancelled'):
                raise ValidationError(
                    _('مرفوض: لا يمكن تعديل سطور قيد تم ترحيله أو إلغاؤه.')
                )

        # 1. منع الترحيل على حسابات تجميعية (غير ختامية)
        if self.account_id and not self.account.is_leaf:
            raise ValidationError(
                _('لا يمكن الترحيل على حساب تجميعي. يجب اختيار حساب ختامي (فرعي).')
            )

        # 2. منع القيم السالبة
        if self.debit < 0 or self.credit < 0:
            raise ValidationError(
                _('لا يمكن إدخال قيم بالسالب في القيود المحاسبية.')
            )

        # 3. منع سطر واحد من أن يكون مديناً ودائناً في نفس الوقت
        if self.debit > 0 and self.credit > 0:
            raise ValidationError(
                _('السطر الواحد يجب أن يحمل قيمة مدينة أو دائنة، وليس كلاهما.')
            )

        # 4. التوافق مع إعدادات التسوية (Reconciliation & Partners)
        if self.account_id:
            if self.partner and not self.account.allow_reconciliation:
                raise ValidationError(
                    _('لا يمكن تحديد شريك (عميل/مورد) لحساب لا يقبل التسوية. '
                      'الرجاء تفعيل خاصية "يقبل التسوية" على الحساب من دليل الحسابات أولاً.')
                )

            if self.account.allow_reconciliation and not self.partner:
                raise ValidationError(
                    _('هذا الحساب مخصص للعملاء/الموردين ويقبل التسوية — '
                      'تحديد الشريك (Partner) إلزامي.')
                )