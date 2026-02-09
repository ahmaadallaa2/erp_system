from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # عرض اليوزر نيم في القائمة
    list_display = ('username', 'email', 'full_name', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('username',)

    # التعديل: جانغو بيعرف يتعامل مع اليوزر نيم لوحده في الـ fieldsets
    # فممكن نعتمد على الإعدادات الافتراضية أو نخصصها لو حبينا نضيف phone
    fieldsets = (
        (None, {'fields': ('username', 'password')}), # رجعنا username هنا
        (('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'full_name', 'phone', 'job_title')}),
        (('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (('Important dates'), {'fields': ('last_login', 'date_joined', 'created_at')}),
    )