from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

class Sequence(models.Model):
    """
    موديل لتوليد الأرقام التسلسلية للمستندات (فواتير، أذونات مخزن، إلخ).
    يضمن عدم تكرار الأرقام حتى مع الضغط العالي.
    """
    key = models.CharField(
        _("كود التسلسل"), 
        max_length=50, 
        unique=True, 
        help_text=_("مفتاح فريد لتمييز نوع المستند، مثل: invoice, product_sku")
    )
    
    prefix = models.CharField(
        _("البادئة"), 
        max_length=20, 
        default="", 
        blank=True,
        help_text=_("نص يظهر قبل الرقم، مثل: INV-")
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
        return f"{self.key} ({self.prefix}{str(self.current_value).zfill(self.padding)})"

    @classmethod
    def next_number(cls, key, prefix="DOC-", padding=5):
        """
        دالة ذرية (Atomic) للحصول على الرقم التالي.
        تقوم بإنشاء العداد لو لم يكن موجوداً، أو تحديثه لو كان موجوداً.
        
        الاستخدام:
        new_inv_no = Sequence.next_number('invoice', 'INV-', 6)
        # النتيجة: INV-000001
        """
        with transaction.atomic():
            # 1. محاولة جلب العداد وقفل الصف (Lock) لمنع التداخل
            sequence, created = cls.objects.select_for_update().get_or_create(
                key=key,
                defaults={'prefix': prefix, 'padding': padding}
            )
            
            # 2. زيادة العداد
            sequence.current_value += 1
            sequence.save()
            
            # 3. تنسيق الرقم النهائي (Pad with zeros)
            # مثال: 1 -> "00001"
            number_str = str(sequence.current_value).zfill(sequence.padding)
            
            # 4. دمج البادئة مع الرقم
            # النتيجة النهائية: INV-00001
            full_sequence = f"{sequence.prefix}{number_str}"
            
            return full_sequence