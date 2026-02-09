from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from .models import Company, Branch, SystemSetting, Sequence, Attachment, AuditLog

# --- 1. الـ Inlines (يجب تعريفها في البداية) ---

class AttachmentInline(GenericTabularInline):
    """
    يسمح بإظهار خانة رفع الملفات داخل أي صفحة أدمن أخرى (مثل الشركة أو المنتج).
    """
    model = Attachment
    extra = 1
    # تأكد أن اسم الحقل هنا يطابق الموجود في الموديل (description أو note)
    fields = ('file', 'name', 'note') 
    ct_field = "content_type"
    ct_fk_field = "object_id"


class BranchInline(admin.TabularInline):
    """
    يسمح بإضافة الفروع مباشرة من صفحة تعديل الشركة.
    """
    model = Branch
    extra = 0          # لا تظهر صفوف فارغة افتراضياً
    fields = ('name', 'code', 'phone', 'is_active')
    show_change_link = True  # زر لتعديل تفاصيل الفرع


# --- 2. أدمن الشركة ---
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'tax_number')
    
    # دمجنا الفروع والمرفقات هنا
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


# --- 3. أدمن الفروع ---
@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'phone', 'is_active')
    list_filter = ('company', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'phone')
    ordering = ('company', 'name')
    
    # يمكن إضافة المرفقات للفروع أيضاً إذا أردت
    inlines = [AttachmentInline]
    
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات الفرع', {
            'fields': ('company', 'name', 'code', 'is_active')
        }),
        ('الاتصال', {
            'fields': ('phone', 'address')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


# --- 4. أدمن إعدادات النظام ---
@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('system_name', 'default_currency', 'is_maintenance_mode')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    def has_add_permission(self, request):
        # منع إضافة أكثر من صف للإعدادات (Singleton Pattern)
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


# --- 5. أدمن التسلسل الرقمي ---
@admin.register(Sequence)
class SequenceAdmin(admin.ModelAdmin):
    list_display = ('key', 'current_value', 'prefix', 'formatted_next')
    search_fields = ('key', 'prefix')
    readonly_fields = ('formatted_next',)

    # دالة لعرض شكل الرقم القادم
    def formatted_next(self, obj):
        return f"{obj.prefix}{str(obj.current_value + 1).zfill(obj.padding)}"
    formatted_next.short_description = "الرقم التالي المتوقع"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'content_type', 'object_id', 'short_changes')
    list_filter = ('action', 'timestamp', 'content_type', 'user')
    search_fields = ('object_id', 'user__email', 'changes')
    
    # منع الإضافة والتعديل والحذف نهائياً (سجل للقراءة فقط)
    def has_add_permission(self, request):
        return False
    def has_change_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

    def short_changes(self, obj):
        """عرض مختصر للتغييرات"""
        if obj.changes:
            return str(obj.changes)[:50] + "..."
        return "-"
    short_changes.short_description = "التغييرات"