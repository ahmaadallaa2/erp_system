import json
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin, TabularInline # إضافة TabularInline الخاصة بـ Unfold
from .models import Company, Branch, SystemSetting, Sequence, Attachment, AuditLog

# ==========================================
# 1. الـ Inlines
# ==========================================

class AttachmentInline(GenericTabularInline):
    """
    خانة رفع الملفات داخل أي صفحة أدمن أخرى.
    """
    model = Attachment
    extra = 1
    fields = ('file', 'name', 'note') 
    ct_field = "content_type"
    ct_fk_field = "object_id"


class BranchInline(TabularInline): # استخدام TabularInline الخاصة بـ Unfold
    """
    إضافة الفروع مباشرة من صفحة تعديل الشركة.
    """
    model = Branch
    extra = 0
    fields = ('name', 'code', 'phone', 'is_active')
    show_change_link = True 


# ==========================================
# 2. أدمن الشركة والفروع
# ==========================================

@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'tax_number')
    inlines = [BranchInline, AttachmentInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'logo', 'email', 'phone', 'website', 'address')
        }),
        ('البيانات القانونية', {
            'fields': ('tax_number', 'commercial_record'),
            'classes': ('collapse',),
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Branch)
class BranchAdmin(ModelAdmin):
    list_display = ('name', 'code', 'company', 'phone', 'is_active')
    list_filter = ('company', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'phone')
    ordering = ('company', 'name')
    inlines = [AttachmentInline]
    
    # التعديل هنا: إضافة 'code' للحقول غير القابلة للتعديل
    readonly_fields = ('code', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات الفرع', {
            # تريكة الـ UI: وضع الاسم والكود في سطر واحد
            'fields': (
                'company', 
                ('name', 'code'), 
                'is_active'
            )
        }),
        ('الاتصال', {
            'fields': ('phone', 'address')
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'), 
                ('created_by', 'updated_by')
            ),
            'classes': ('collapse',),
        }),
    )


# ==========================================
# 3. إعدادات النظام والتسلسلات
# ==========================================

@admin.register(SystemSetting)
class SystemSettingAdmin(ModelAdmin):
    list_display = ('system_name', 'default_currency', 'is_maintenance_mode')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    # تنسيق شكل الإعدادات في لوحة التحكم
    fieldsets = (
        ('الإعدادات العامة', {
            'fields': ('system_name', 'is_maintenance_mode', 'allow_registration')
        }),
        ('الإعدادات المالية', {
            'fields': ('default_currency', 'default_vat_percentage', 'decimal_places')
        }),
        ('الإعدادات التقنية', {
            'fields': ('session_timeout_minutes', 'created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(Sequence)
class SequenceAdmin(ModelAdmin):
    list_display = ('key', 'current_value', 'prefix', 'formatted_next')
    search_fields = ('key', 'prefix')
    readonly_fields = ('formatted_next',)

    def formatted_next(self, obj):
        return f"{obj.prefix}{str(obj.current_value + 1).zfill(obj.padding)}"
    formatted_next.short_description = "الرقم التالي المتوقع"


# ==========================================
# 4. أدمن سجل التتبع (الصندوق الأسود)
# ==========================================

@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'content_type', 'object_link', 'short_changes')
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('object_id', 'user__username', 'user__email')
    
    readonly_fields = ('user', 'action', 'content_type', 'object_id', 'object_link', 'timestamp', 'ip_address', 'browser_info', 'formatted_changes')
    
    fieldsets = (
        ('معلومات الحركة', {
            'fields': ('user', 'action', 'timestamp', 'ip_address', 'browser_info')
        }),
        ('السجل المرتبط', {
            'fields': ('content_type', 'object_id', 'object_link')
        }),
        ('تفاصيل التغييرات', {
            'fields': ('formatted_changes',)
        }),
    )

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False

    def short_changes(self, obj):
        if obj.changes: return str(obj.changes)[:50] + "..."
        return "-"
    short_changes.short_description = "ملخص التغييرات"

    def formatted_changes(self, obj):
        if obj.changes:
            pretty_json = json.dumps(obj.changes, indent=4, ensure_ascii=False)
            return format_html('<pre style="direction: ltr; text-align: left; background-color: #f8f9fa; padding: 10px; border-radius: 5px;">{}</pre>', pretty_json)
        return "لا توجد تغييرات"
    formatted_changes.short_description = "التغييرات (JSON)"

    def object_link(self, obj):
        if obj.content_object:
            try:
                url = reverse(f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change", args=[obj.object_id])
                return format_html('<a href="{}" style="font-weight: bold; color: #007bff;">عرض السجل &#8594;</a>', url)
            except:
                return str(obj.content_object)
        return format_html('<span style="color: red;">(محذوف)</span>')
    object_link.short_description = "رابط السجل"