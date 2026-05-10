from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.core.models import Attachment


@admin.register(Attachment)
class AttachmentAdmin(ModelAdmin):
    list_display = (
        'name',
        'file_type',
        'content_type',
        'object_id',
        'created_at',
    )
    list_filter = (
        'content_type',
        'file_type',
        'created_at',
    )
    search_fields = (
        'name',
        'note',
        'object_id',
        'file_type',
    )
    readonly_fields = (
        'file_type',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        ('بيانات المرفق', {
            'fields': (
                'content_type',
                'object_id',
                'file',
                'name',
                'note',
                'file_type',
            )
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ),
            'classes': ('collapse',),
        }),
    )
