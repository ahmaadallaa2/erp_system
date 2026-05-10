import json
from django.contrib import admin
from django.urls import NoReverseMatch, reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.core.models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = (
        'timestamp',
        'user',
        'action',
        'content_type',
        'object_link',
        'short_changes',
    )
    list_filter = ('action', 'timestamp', 'content_type')
    search_fields = ('object_id', 'user__username', 'user__email')

    readonly_fields = (
        'user',
        'action',
        'content_type',
        'object_id',
        'object_link',
        'timestamp',
        'ip_address',
        'browser_info',
        'formatted_changes',
    )

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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.display(description="ملخص التغييرات")
    def short_changes(self, obj):
        if obj.changes:
            text = str(obj.changes)
            return text[:50] + "..." if len(text) > 50 else text
        return "-"

    @admin.display(description="التغييرات (JSON)")
    def formatted_changes(self, obj):
        if obj.changes:
            pretty_json = json.dumps(obj.changes, indent=4, ensure_ascii=False)
            return format_html(
                '<pre style="direction: ltr; text-align: left; background-color: #f8f9fa; padding: 10px; border-radius: 5px; white-space: pre-wrap;">{}</pre>',
                pretty_json
            )
        return "لا توجد تغييرات"

    @admin.display(description="رابط السجل")
    def object_link(self, obj):
        if obj.content_object:
            try:
                url = reverse(
                    f"admin:{obj.content_type.app_label}_{obj.content_type.model}_change",
                    args=[obj.object_id]
                )
                return format_html(
                    '<a href="{}" style="font-weight: bold; color: #007bff;">عرض السجل &#8594;</a>',
                    url
                )
            except NoReverseMatch:
                return str(obj.content_object)
            except Exception:
                return str(obj.content_object)

        return format_html('<span style="color: red;">{}</span>', '(محذوف)')
