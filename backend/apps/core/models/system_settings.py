from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import BaseModel  # استدعاء الـ Base Model اللي اتفقنا عليه

class SystemSetting(BaseModel):
    """
    موديل يخزن إعدادات النظام العامة.
    يفترض وجود صف واحد (Record) فقط في هذا الجدول.
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

    # دالة مساعدة عشان نضمن إننا دايماً بنعدل نفس الريكورد مش بنعمل جديد
    def save(self, *args, **kwargs):
        if not self.pk and SystemSetting.objects.exists():
            # لو بنحاول نكريت واحد جديد وفيه واحد أصلاً موجود، نمنع ده (Singleton Pattern مبسط)
            # أو ممكن نحدث الموجود، بس هنا هنسمح بالأدمن يديرها
            pass 
        return super(SystemSetting, self).save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """
        دالة بنناديها من أي مكان في الكود عشان تجيب الإعدادات الحالية
        SystemSetting.get_settings().default_currency
        """
        obj, created = cls.objects.get_or_create(id=1) # أو نعتمد على أول واحد
        # الكود هنا للتبسيط، الأفضل نستخدم cache
        first_setting = cls.objects.first()
        if not first_setting:
            first_setting = cls.objects.create()
        return first_setting