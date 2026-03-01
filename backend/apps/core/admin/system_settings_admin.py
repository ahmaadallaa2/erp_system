import json
from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.urls import reverse
from django.utils.html import format_html
from unfold.admin import ModelAdmin # إضافة TabularInline الخاصة بـ Unfold
from ..models import SystemSetting

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