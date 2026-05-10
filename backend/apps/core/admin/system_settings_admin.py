from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.core.models import SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(ModelAdmin):
    list_display = ('system_name', 'default_currency', 'is_maintenance_mode')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

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

    def has_delete_permission(self, request, obj=None):
        return False
