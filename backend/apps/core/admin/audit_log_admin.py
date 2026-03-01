import json
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from ..models import AuditLog

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
        
        # التعديل هنا: وضعنا {} ومررنا كلمة (محذوف) كـ Argument
        return format_html('<span style="color: red;">{}</span>', '(محذوف)')
        
    object_link.short_description = "رابط السجل"