from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.core.admin.inlines import AttachmentInline
from apps.core.models import Branch


@admin.register(Branch)
class BranchAdmin(ModelAdmin):
    list_display = ('name', 'code', 'company', 'phone', 'is_active')
    list_filter = ('company', 'is_active', 'created_at')
    search_fields = ('name', 'code', 'phone', 'company__name')
    ordering = ('company', 'name')
    inlines = [AttachmentInline]

    readonly_fields = ('code', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات الفرع', {
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
