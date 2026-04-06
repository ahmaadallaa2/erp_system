from decimal import Decimal
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from django.db.models.functions import Coalesce

from unfold.admin import ModelAdmin, TabularInline
from apps.accounting.models.entry import JournalEntry, JournalItem


# =============================================================================
# Inline: سطور القيد
# =============================================================================
class JournalItemInline(TabularInline):
    model = JournalItem
    extra = 2
    fields = ('account', 'partner', 'description', 'debit', 'credit')
    autocomplete_fields = ('account', 'partner')

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return ('account', 'partner', 'description', 'debit', 'credit')
        return ()

    def has_add_permission(self, request, obj=None):
        # منع إضافة قبل حفظ القيد
        if not obj:
            return False
        if obj.status in ('posted', 'cancelled'):
            return False
        return super().has_add_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)


# =============================================================================
# Admin: القيد الرئيسي
# =============================================================================
@admin.register(JournalEntry)
class JournalEntryAdmin(ModelAdmin):

    list_display = (
        'company',
        'entry_number',
        'journal',
        'date',
        'reference',
        'get_status_badge',
        'get_total_debit',
        'get_total_credit',
    )

    list_filter = (
        'company',
        'status',
        'journal',
        'date'
    )

    search_fields = (
        'entry_number',
        'reference',
        'notes',
        'journal__name'
    )

    ordering = ('-date', '-id')

    inlines = [JournalItemInline]

    readonly_fields = (
        'entry_number',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        (_('البيانات الأساسية'), {
            'fields': (
                'company',
                ('entry_number', 'date'),
                ('journal', 'status'),
            )
        }),
        (_('الارتباطات والملاحظات'), {
            'fields': ('reference', 'notes')
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),
            'fields': (
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            )
        }),
    )

    # =========================================================================
    # 🚀 Optimization
    # =========================================================================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('company', 'journal').annotate(
            annotated_total_debit=Coalesce(Sum('items__debit'), Decimal('0.00')),
            annotated_total_credit=Coalesce(Sum('items__credit'), Decimal('0.00'))
        )

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return (
                'company', 'entry_number', 'journal', 'date',
                'reference', 'status', 'notes',
                'created_at', 'updated_at',
                'created_by', 'updated_by'
            )
        return self.readonly_fields

    # =========================================================================
    # Actions
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
    # Computed Columns
    # =========================================================================
    @admin.display(description=_('الحالة'), ordering='status')
    def get_status_badge(self, obj):
        styles = {
            'draft':     ('#e65100', '#fff3e0', _('مسودة')),
            'posted':    ('#1b5e20', '#e8f5e9', _('مُرحّل')),
            'cancelled': ('#b71c1c', '#ffebee', _('ملغي')),
        }
        text_color, bg_color, label = styles.get(obj.status, ('#333', '#eee', obj.status))

        return format_html(
            '<span style="background-color: {}; color: {}; padding: 2px 10px; border-radius: 12px; font-weight: bold;">{}</span>',
            bg_color, text_color, label
        )

    @admin.display(description=_('إجمالي المدين'), ordering='annotated_total_debit')
    def get_total_debit(self, obj):
        total = getattr(obj, 'annotated_total_debit', Decimal('0.00'))
        return format_html(
            '<span style="color: #1565c0; font-weight: bold;">{}</span>',
            f"{total:,.2f}"
        )

    @admin.display(description=_('إجمالي الدائن'), ordering='annotated_total_credit')
    def get_total_credit(self, obj):
        total = getattr(obj, 'annotated_total_credit', Decimal('0.00'))
        return format_html(
            '<span style="color: #6a1b9a; font-weight: bold;">{}</span>',
            f"{total:,.2f}"
        )

    # =========================================================================
    # Save
    # =========================================================================
    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)