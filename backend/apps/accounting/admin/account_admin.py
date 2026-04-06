from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin

from apps.accounting.models.account import Account


@admin.register(Account)
class AccountAdmin(ModelAdmin):
    # =========================================================================
    # 1. إعدادات القائمة (List View)
    # =========================================================================
    list_display = (
        'company',
        'code',
        'name',
        'account_type',
        'normal_balance',
        'parent',
        'get_level',
        'is_postable',
        'allow_reconciliation',
        'is_active',
        'get_current_balance',
    )

    list_filter = (
        'company',
        'account_type',
        'normal_balance',
        'is_postable',
        'is_active',
        'allow_reconciliation',
    )

    list_editable = ('is_active',)
    search_fields = ('code', 'name', 'company__name', 'parent__name')
    ordering = ('company', 'code')

    autocomplete_fields = ('company', 'parent')

    readonly_fields = (
        'get_current_balance',
        'get_level',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    # =========================================================================
    # 2. تنظيم الحقول (Fieldsets)
    # =========================================================================
    fieldsets = (
        (_('البيانات الأساسية'), {
            'fields': (
                'company',
                ('code', 'name'),
                ('account_type', 'normal_balance'),
                'parent',
            )
        }),
        (_('إعدادات المحاسبة'), {
            'fields': (
                ('is_postable', 'allow_reconciliation', 'is_active'),
            )
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),
            'fields': (
                'get_level',
                'get_current_balance',
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            )
        }),
    )

    # =========================================================================
    # 3. الأعمدة المحسوبة (Computed Columns)
    # =========================================================================
    @admin.display(description=_('المستوى'), ordering='code')
    def get_level(self, obj):
        level = obj.level
        indent = '—' * level
        return f"{indent} {level}" if level > 0 else '0 (جذر)'

    @admin.display(description=_('الرصيد الفعلي'))
    def get_current_balance(self, obj):
        """
        للحسابات القابلة للترحيل فقط.
        الحسابات التجميعية لا نحسب رصيدها هنا لتجنب البطء وسوء الفهم.
        """
        if not obj.is_postable:
            return format_html(
                '<span style="color: #757575; font-style: italic;">{}</span>',
                'حساب تجميعي'
            )

        balance = obj.current_balance

        if balance > 0:
            color = '#2e7d32'  # أخضر
        elif balance < 0:
            color = '#c62828'  # أحمر
        else:
            color = '#757575'  # رمادي

        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            f"{balance:,.2f}"
        )

    # =========================================================================
    # 4. الحفظ
    # =========================================================================
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)