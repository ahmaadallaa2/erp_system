# apps/accounting/admin/entry_admin.py

from decimal import Decimal
from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import Coalesce

from unfold.admin import ModelAdmin, TabularInline
from apps.accounting.models.entry import JournalEntry, JournalItem


# =============================================================================
# Inline: سطور القيد
# =============================================================================
class JournalItemInline(TabularInline):
    model  = JournalItem
    extra  = 2  # سطرين افتراضيين (مدين + دائن)
    fields = ('account', 'partner', 'description', 'debit', 'credit')
    autocomplete_fields = ('account', 'partner')

    def get_readonly_fields(self, request, obj=None):
        """
        لو القيد مُرحّل أو ملغي → كل سطور الـ inline تبقى للقراءة فقط.
        يمنع التعديل المباشر من الـ Admin متجاوزاً الـ clean().
        """
        if obj and obj.status in ('posted', 'cancelled'):
            return ('account', 'partner', 'description', 'debit', 'credit')
        return ()

    def has_add_permission(self, request, obj=None):
        """منع إضافة سطور جديدة لقيد مُرحّل أو ملغي."""
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """منع حذف سطور من قيد مُرحّل أو ملغي."""
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)


# =============================================================================
# Admin: القيد الرئيسي
# =============================================================================
@admin.register(JournalEntry)
class JournalEntryAdmin(ModelAdmin):

    # =========================================================================
    # 1. إعدادات القايمة (List View)
    # =========================================================================
    list_display  = (
        'entry_number', 'journal', 'date',
        'reference', 'get_status_badge',
        'get_total_debit', 'get_total_credit',
    )
    list_filter   = ('status', 'journal', 'date')
    search_fields = ('entry_number', 'reference', 'notes')
    ordering      = ('-date', '-id')

    inlines       = [JournalItemInline]
    
    # readonly_fields الأساسية (التي لا تتغير أبداً)
    readonly_fields = ('entry_number', 'created_at', 'updated_at')

    # =========================================================================
    # 2. تنظيم الحقول (Fieldsets)
    # =========================================================================
    fieldsets = (
        (_('البيانات الأساسية'), {
            'fields': (
                ('entry_number', 'date'),
                ('journal', 'status'),
            )
        }),
        (_('الارتباطات والملاحظات'), {
            'fields': ('reference', 'notes')
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    # =========================================================================
    # 🚀 تحسين الأداء والحماية (Query Optimization & Security)
    # =========================================================================
    def get_queryset(self, request):
        """
        حساب إجمالي المدين والدائن لكل القيود في استعلام واحد فقط (1 Query)
        مما يعالج مشكلة الـ N+1 Query Problem بالكامل.
        """
        qs = super().get_queryset(request)
        return qs.annotate(
            annotated_total_debit=Coalesce(Sum('items__debit'), Decimal('0.00')),
            annotated_total_credit=Coalesce(Sum('items__credit'), Decimal('0.00'))
        )

    def get_readonly_fields(self, request, obj=None):
        """
        إغلاق رأس القيد (Journal Entry) بالكامل لو كان مُرحل أو ملغي.
        هذا يمنع التلاعب بتاريخ القيد أو الدفتر بعد الترحيل.
        """
        if obj and obj.status in ('posted', 'cancelled'):
            # إرجاع كل الحقول كـ Read-only
            return ('entry_number', 'journal', 'date', 'reference', 'status', 'notes', 'created_at', 'updated_at')
        return self.readonly_fields

    # =========================================================================
    # 3. Actions: ترحيل وإلغاء من القايمة
    # =========================================================================
    actions = ('action_post', 'action_cancel')

    @admin.action(description=_('✅ ترحيل القيود المحددة'))
    def action_post(self, request, queryset):
        success, errors = 0, []
        for entry in queryset.filter(status='draft'):
            try:
                entry.post()
                success += 1
            except Exception as e:
                # استخدمنا str(e) لاستخراج الرسالة بشكل نظيف
                errors.append(f"{entry.entry_number}: {str(e)}")

        if success:
            self.message_user(
                request,
                _(f'تم ترحيل {success} قيد بنجاح.'),
                messages.SUCCESS
            )
        for error in errors:
            self.message_user(request, error, messages.ERROR)

    @admin.action(description=_('❌ إلغاء القيود المحددة'))
    def action_cancel(self, request, queryset):
        success, errors = 0, []
        for entry in queryset.filter(status='draft'):
            try:
                entry.cancel()
                success += 1
            except Exception as e:
                errors.append(f"{entry.entry_number}: {str(e)}")

        if success:
            self.message_user(
                request,
                _(f'تم إلغاء {success} قيد بنجاح.'),
                messages.SUCCESS
            )
        for error in errors:
            self.message_user(request, error, messages.ERROR)

    # =========================================================================
    # 4. الأعمدة المحسوبة (Computed Columns)
    # =========================================================================
    @admin.display(description=_('الحالة'), ordering='status')
    def get_status_badge(self, obj):
        """يعرض حالة القيد كـ badge ملون."""
        styles = {
            'draft':     ('#e65100', '#fff3e0', _('مسودة')),
            'posted':    ('#1b5e20', '#e8f5e9', _('مُرحّل')),
            'cancelled': ('#b71c1c', '#ffebee', _('ملغي')),
        }
        text_color, bg_color, label = styles.get(obj.status, ('#333', '#eee', obj.status))
        return format_html(
            '<span style="'
            'background-color: {}; color: {}; '
            'padding: 2px 10px; border-radius: 12px; '
            'font-size: 12px; font-weight: bold;">'
            '{}</span>',
            bg_color, text_color, label
        )

    @admin.display(description=_('إجمالي المدين'), ordering='annotated_total_debit')
    def get_total_debit(self, obj):
        # نقرأ القيمة من المتغير المحسوب في الـ get_queryset مباشرة
        total = getattr(obj, 'annotated_total_debit', Decimal('0.00'))
        return format_html(
            '<span style="color: #1565c0; font-weight: bold;">{}</span>',
            f"{total:,.2f}"
        )

    @admin.display(description=_('إجمالي الدائن'), ordering='annotated_total_credit')
    def get_total_credit(self, obj):
        # نقرأ القيمة من المتغير المحسوب في الـ get_queryset مباشرة
        total = getattr(obj, 'annotated_total_credit', Decimal('0.00'))
        return format_html(
            '<span style="color: #6a1b9a; font-weight: bold;">{}</span>',
            f"{total:,.2f}"
        )