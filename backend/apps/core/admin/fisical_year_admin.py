from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import FiscalYear


@admin.register(FiscalYear)
class FiscalYearAdmin(ModelAdmin):
    list_display = (
        'name',
        'company',
        'start_date',
        'end_date',
        'is_active',
        'is_closed',
    )
    list_filter = (
        'company',
        'is_active',
        'is_closed',
        'start_date',
        'end_date',
    )
    search_fields = (
        'name',
        'company__name',
    )
    ordering = ('-start_date',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        ('بيانات السنة المالية', {
            'fields': (
                'company',
                'name',
                ('start_date', 'end_date'),
            )
        }),
        ('الحالة', {
            'fields': (
                'is_active',
                'is_closed',
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