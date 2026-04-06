from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from unfold.admin import ModelAdmin

from apps.accounting.models.journal import Journal


@admin.register(Journal)
class JournalAdmin(ModelAdmin):
    # =========================================================================
    # 1. إعدادات القائمة (List View)
    # =========================================================================
    list_display = (
        'company',
        'code',
        'name',
        'get_type_badge',
        'default_account',
        'is_active',
        'get_entries_count',
    )

    list_filter = (
        'company',
        'type',
        'is_active',
    )

    search_fields = (
        'code',
        'name',
        'company__name',
        'default_account__name',
        'default_account__code',
    )

    ordering = ('company', 'code')

    autocomplete_fields = ('company', 'default_account')

    readonly_fields = (
        'get_entries_count',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    # =========================================================================
    # 2. تنظيم الحقول (Fieldsets)
    # =========================================================================
    fieldsets = (
        (_('بيانات الدفتر'), {
            'fields': (
                'company',
                ('code', 'name'),
                ('type', 'is_active'),
                'default_account',
            )
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),
            'fields': (
                'get_entries_count',
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            )
        }),
    )

    # =========================================================================
    # 3. تحسين الأداء (Query Optimization)
    # =========================================================================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'default_account').annotate(
            entries_count=Count('entries')
        )

    # =========================================================================
    # 4. الأعمدة المحسوبة (Computed Columns)
    # =========================================================================
    @admin.display(description=_('النوع'))
    def get_type_badge(self, obj):
        colors = {
            'sale': ('#1b5e20', '#e8f5e9'),
            'purchase': ('#b71c1c', '#ffebee'),
            'cash': ('#e65100', '#fff3e0'),
            'bank': ('#0d47a1', '#e3f2fd'),
            'general': ('#4a148c', '#f3e5f5'),
        }
        text_color, bg_color = colors.get(obj.type, ('#333', '#eee'))

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;">{}</span>',
            bg_color,
            text_color,
            obj.get_type_display()
        )

    @admin.display(description=_('عدد القيود'), ordering='entries_count')
    def get_entries_count(self, obj):
        if not obj or not obj.pk:
            return format_html('<span style="color: #9e9e9e;">{}</span>', '—')

        count = getattr(obj, 'entries_count', 0)

        if count == 0:
            return format_html('<span style="color: #9e9e9e;">{}</span>', '—')

        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )

    # =========================================================================
    # 5. الحفظ
    # =========================================================================
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)