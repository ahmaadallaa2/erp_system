from django.db import models
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from apps.core.models.base import BaseModel

class SystemSetting(BaseModel):
    """
    موديل يخزن إعدادات النظام العامة (Singleton Pattern).
    يوجد صف واحد فقط، ويتم تخزينه في الذاكرة (Cache) لسرعة الأداء.
    """
    # --- إعدادات عامة ---
    system_name = models.CharField(_("اسم النظام"), max_length=100, default="My ERP")
    is_maintenance_mode = models.BooleanField(_("وضع الصيانة"), default=False, help_text=_("إذا تم تفعيله، لن يتمكن الموظفون من الدخول."))
    allow_registration = models.BooleanField(_("السماح بالتسجيل"), default=False, help_text=_("هل يسمح للمستخدمين الجدد بإنشاء حسابات بأنفسهم؟"))

    # --- إعدادات مالية ---
    default_currency = models.CharField(_("العملة الافتراضية"), max_length=10, default="EGP")
    default_vat_percentage = models.DecimalField(_("نسبة ضريبة القيمة المضافة (%)"), max_digits=5, decimal_places=2, default=14.00)
    decimal_places = models.PositiveSmallIntegerField(_("عدد الكسور العشرية"), default=2, help_text=_("للأرقام المالية (مثلاً 2 لـ 10.50)"))

    # --- إعدادات تقنية ---
    session_timeout_minutes = models.PositiveIntegerField(_("وقت انتهاء الجلسة (دقيقة)"), default=60)
    
    class Meta:
        verbose_name = _("إعدادات النظام")
        verbose_name_plural = _("إعدادات النظام")

    def __str__(self):
        return f"Settings ({self.system_name})"

    def clean(self):
        """
        التحقق قبل الحفظ (يمنع حفظ السجل من لوحة الإدارة إذا كان هناك سجل بالفعل).
        """
        if not self.pk and SystemSetting.objects.exists():
            raise ValidationError(_("لا يمكن إنشاء أكثر من سجل لإعدادات النظام. يرجى تعديل السجل الحالي."))
        super().clean()

    def save(self, *args, **kwargs):
        self.clean() # تأكيد تشغيل التحقق
        super().save(*args, **kwargs)
        # تفريغ الكاش فوراً بمجرد حفظ أي تعديل لضمان قراءة البيانات الجديدة
        cache.delete('core_system_settings')

    @classmethod
    def get_settings(cls):
        """
        دالة ذكية لجلب الإعدادات من الذاكرة العشوائية (Cache) بدلاً من الداتابيز.
        الاستخدام في أي مكان: SystemSetting.get_settings().default_currency
        """
        # 1. محاولة جلب الإعدادات من الكاش
        settings_obj = cache.get('core_system_settings')
        
        # 2. لو مش في الكاش، هنجيبها من الداتابيز
        if not settings_obj:
            settings_obj = cls.objects.first()
            
            # 3. لو الداتابيز فاضية تماماً (أول تشغيل للنظام)، ننشئ السجل الافتراضي
            if not settings_obj:
                settings_obj = cls.objects.create()
                
            # 4. نحفظ السجل في الكاش لمدة 24 ساعة (أو لحين التعديل)
            cache.set('core_system_settings', settings_obj, timeout=60 * 60 * 24)
            
        return settings_obj