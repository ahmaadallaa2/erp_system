from django.db import models
from django.utils.translation import gettext_lazy as _
from .user import User  # <--- استيراد User من الملف المجاور

class Profile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='profile',
        verbose_name=_("المستخدم")
    )
    
    avatar = models.ImageField(
        _("الصورة الشخصية"), 
        upload_to='users/avatars/', 
        default='users/avatars/default.png',
        null=True, 
        blank=True
    )
    
    bio = models.TextField(_("نبذة تعريفية"), max_length=500, blank=True)
    birth_date = models.DateField(_("تاريخ الميلاد"), null=True, blank=True)
    address = models.CharField(_("العنوان"), max_length=255, blank=True)
    
    def __str__(self):
        return f"ملف: {self.user.email}"