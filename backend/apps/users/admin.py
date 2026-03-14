from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

# --- استيرادات Unfold ---
from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm, 
    UserChangeForm as BaseUserChangeForm, 
    UserCreationForm as BaseUserCreationForm
)

from .models import User

# ==========================================
# 1. إنشاء نماذج (Forms) مخصصة لتفهم حقولك الجديدة
# ==========================================
class CustomUserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'

class CustomUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        # بنقول للفورم: دي الحقول اللي هتسألي عليها وإنتي بتكريتي اليوزر (جانجو هيضيف password1 و 2 أوتوماتيك)
        fields = ('email', 'full_name', 'user_type', 'company', 'branch')


# ==========================================
# 2. إعدادات الـ Admin
# ==========================================
@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin): 
    # استخدام النماذج المخصصة اللي لسه عاملينها
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    # القائمة الخارجية 
    list_display = ('email', 'full_name', 'user_type', 'company', 'branch', 'is_active')
    list_filter = ('user_type', 'company', 'branch', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name', 'phone')
    ordering = ('-date_joined',)

    # صفحة "تعديل" مستخدم حالي (Fieldsets)
    fieldsets = (
        (None, {'fields': ('email', 'password')}), 
        (_('البيانات الشخصية'), {
            'fields': ('full_name', 'phone', 'job_title') 
        }),
        (_('هيكل العمل والصلاحيات'), {
            'fields': ('user_type', 'company', 'branch')
        }),
        (_('صلاحيات دجانغو'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',), 
        }),
        (_('التواريخ الهامة'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    # صفحة "إنشاء" مستخدم جديد (Add Fieldsets)
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            # التعديل السحري هنا: استخدام password1 و password2 بدلاً من password
            'fields': ('email', 'full_name', 'user_type', 'company', 'branch', 'password1', 'password2'),
        }),
    )

    # حقول للقراءة فقط
    readonly_fields = ('last_login', 'date_joined')