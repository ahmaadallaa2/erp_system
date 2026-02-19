from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

# --- استيرادات Unfold ---
from unfold.admin import ModelAdmin, StackedInline
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import User, Profile

# --- 1. إعداد عرض البروفايل (Inline) ---
# يجب تعريفه قبل UserAdmin
class ProfileInline(StackedInline): # تم التبديل إلى Unfold StackedInline
    model = Profile
    can_delete = False
    verbose_name_plural = _('الملف الشخصي')
    fk_name = 'user'  # تحديد الربط بوضوح


# --- 2. إعداد أدمن المستخدمين ---
@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin): # دمج BaseUserAdmin مع ModelAdmin الخاص بـ Unfold
    
    # استخدام نماذج Unfold لتحسين شكل حقول الإدخال وتغيير كلمة المرور
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    # الأعمدة التي تظهر في القائمة الخارجية
    list_display = ('username', 'email', 'full_name', 'is_staff', 'created_at')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'email', 'full_name', 'phone')
    ordering = ('username',)

    # ربط البروفايل ليظهر داخل صفحة المستخدم
    inlines = [ProfileInline]

    # تقسيم الحقول داخل صفحة التعديل
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'full_name', 'phone', 'job_title')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined', 'created_at')
        }),
    )

    # حقول للقراءة فقط (لتجنب التعديل الخطأ على التواريخ)
    readonly_fields = ('last_login', 'date_joined', 'created_at')