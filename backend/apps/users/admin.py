from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

# --- استيرادات Unfold ---
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin): 
    # استخدام نماذج Unfold لتحسين شكل حقول الإدخال
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    # 1. القائمة الخارجية (تم استبدال username بـ email وإضافة حقول الـ ERP)
    list_display = ('email', 'full_name', 'user_type', 'company', 'branch', 'is_active')
    list_filter = ('user_type', 'company', 'branch', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)

    # 2. صفحة "تعديل" مستخدم حالي (Fieldsets)
    fieldsets = (
        (None, {'fields': ('email', 'password')}), # الإيميل هو الأساس الآن
        (_('البيانات الشخصية'), {
            'fields': ('full_name', 'phone', 'job_title') 
        }),
        (_('هيكل العمل والصلاحيات'), {
            'fields': ('user_type', 'company', 'branch')
        }),
        (_('صلاحيات دجانغو'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',), # جعلها قابلة للطي لتقليل الزحمة
        }),
        (_('التواريخ الهامة'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    # 3. صفحة "إنشاء" مستخدم جديد (Add Fieldsets) - إضافة حتمية لمنع الأخطاء!
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password', 'full_name', 'user_type', 'company', 'branch'),
        }),
    )

    # حقول للقراءة فقط
    readonly_fields = ('last_login', 'date_joined')