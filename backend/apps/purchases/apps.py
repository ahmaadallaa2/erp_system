from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class PurchasesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    
    # التعديل الأهم: كتابة المسار الكامل للتطبيق
    name = 'apps.purchases' 
    
    # الاسم اللي هيظهر في لوحة التحكم (Admin)
    verbose_name = _("إدارة المشتريات")