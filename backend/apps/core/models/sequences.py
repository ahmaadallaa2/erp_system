from django.db import models, transaction, IntegrityError
from django.utils.translation import gettext_lazy as _

class Sequence(models.Model):
    """
    موديل لتوليد الأرقام التسلسلية للمستندات (فواتير، أذونات مخزن، إلخ).
    يضمن عدم تكرار الأرقام حتى مع الضغط العالي جداً.
    """
    key = models.CharField(
        _("كود التسلسل"), 
        max_length=100, # قمنا بزيادة الطول ليستوعب السنة واسم الفرع
        unique=True, 
        help_text=_("مفتاح فريد لتمييز نوع المستند، مثل: invoice_branch1_2026")
    )
    
    prefix = models.CharField(
        _("البادئة"), 
        max_length=20, 
        default="", 
        blank=True,
        help_text=_("نص يظهر قبل الرقم، مثل: INV-2026-")
    )
    
    current_value = models.PositiveIntegerField(
        _("القيمة الحالية"), 
        default=0
    )
    
    padding = models.PositiveIntegerField(
        _("عدد الخانات"), 
        default=5, 
        help_text=_("عدد الأصفار، 5 تعني 00001")
    )

    class Meta:
        verbose_name = _("عداد تسلسلي")
        verbose_name_plural = _("عدادات تسلسلية")

    def __str__(self):
        number_str = str(self.current_value).zfill(self.padding)
        return f"{self.key} ({self.prefix}{number_str})"

    @classmethod
    def next_number(cls, key, prefix="DOC-", padding=5):
        """
        دالة ذرية (Atomic) للحصول على الرقم التالي.
        """
        with transaction.atomic():
            try:
                # 1. محاولة جلب السجل وقفله لمنع التداخل
                sequence = cls.objects.select_for_update().get(key=key)
            except cls.DoesNotExist:
                # 2. لو لم يكن موجوداً، ننشئه
                try:
                    sequence = cls.objects.create(
                        key=key, 
                        prefix=prefix, 
                        padding=padding, 
                        current_value=0 # يبدأ من صفر لأنه سيزيد في الخطوة التالية
                    )
                except IntegrityError:
                    # في حالة نادرة جداً: مستخدم آخر سبَقنا بجزء من الثانية وأنشأه
                    # نجلب السجل الذي تم إنشاؤه للتو ونقفله
                    sequence = cls.objects.select_for_update().get(key=key)
            
            # 3. زيادة العداد (الآن نحن متأكدون أنه السجل الوحيد وأنه مقفول لنا فقط)
            sequence.current_value += 1
            # 4. حفظ حقل القيمة فقط لسرعة الأداء
            sequence.save(update_fields=['current_value'])
            
            # 5. تنسيق الرقم النهائي
            number_str = str(sequence.current_value).zfill(sequence.padding)
            full_sequence = f"{sequence.prefix}{number_str}"
            
            return full_sequence