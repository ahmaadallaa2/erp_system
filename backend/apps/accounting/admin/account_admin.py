# apps/accounting/admin/account_admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from apps.accounting.models.account import Account


@admin.register(Account)
class AccountAdmin(ModelAdmin):

    # =========================================================================
    # 1. إعدادات القايمة (List View)
    # =========================================================================
    list_display = (
        'code',
        'name',
        'account_type',
        'normal_balance',
        'parent',
        'get_level',
        'is_leaf',
        'allow_reconciliation',
        'is_active',
        'get_current_balance',
    )
    list_filter  = ('account_type', 'normal_balance', 'is_leaf', 'is_active', 'allow_reconciliation')
    list_editable = ('is_active',)  # تعديل سريع من القايمة بدون فتح الحساب
    search_fields = ('code', 'name')
    ordering      = ('code',)

    autocomplete_fields = ('parent',)  # بحث سريع في الحساب الأب لو الشجرة كبرت

    readonly_fields = ('get_current_balance', 'get_level', 'created_at', 'updated_at')

    # =========================================================================
    # 2. تنظيم الحقول (Fieldsets)
    # =========================================================================
    fieldsets = (
        (_('البيانات الأساسية'), {
            'fields': (
                ('code', 'name'),
                ('account_type', 'normal_balance'),
                'parent',
            )
        }),
        (_('إعدادات المحاسبة'), {
            'fields': (
                ('is_leaf', 'allow_reconciliation', 'is_active'),
            )
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),  # مخفية بالافتراضي
            'fields': (
                'get_level',
                'get_current_balance',
                'created_at',
                'updated_at',
            )
        }),
    )

    # =========================================================================
    # 3. الأعمدة المحسوبة (Computed Columns)
    # =========================================================================
    @admin.display(description=_('المستوى'), ordering='code')
    def get_level(self, obj):
        level = obj.level
        indent = '—' * level  # مرئياً يوضح العمق في الشجرة
        return f"{indent} {level}" if level > 0 else '0 (جذر)'

    @admin.display(description=_('الرصيد الفعلي'))
    def get_current_balance(self, obj):
        """
        يعرض الرصيد بلون مناسب:
        - أخضر: رصيد موجب ✅
        - أحمر: رصيد سالب ⚠️
        - رمادي: صفر
        """
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
            f"{balance:,.2f}"  # تنسيق الأرقام: 12,500.00
        )