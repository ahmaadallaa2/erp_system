from django.db import models

class SoftDeleteManager(models.Manager):
    """
    مدير مخصص لاسترجاع البيانات غير المحذوفة فقط بشكل افتراضي.
    """
    def get_queryset(self):
        # أي كويري هتم، هنزود عليها شرط: is_deleted = False
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        # دالة احتياطية لو حبينا نجيب كل الداتا (للتقارير مثلاً)
        return super().get_queryset()