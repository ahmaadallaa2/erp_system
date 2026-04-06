from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline

from .models.sales_invoice import SalesInvoice
from .models.sales_invoice_item import SalesInvoiceItem
from .services.sales_service import SalesService


# ==========================================
# 1. Inline Configuration for Sales Invoice Items
# ==========================================
class SalesInvoiceItemInline(TabularInline):
    model = SalesInvoiceItem
    extra = 1

    fields = ('product', 'quantity', 'unit_price', 'line_total', 'notes')
    readonly_fields = ('line_total',)
    autocomplete_fields = ('product',)

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'posted':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'posted':
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.status == 'posted':
            return False
        return super().has_add_permission(request, obj)


# ==========================================
# 2. Main Sales Invoice Admin Configuration
# ==========================================
@admin.register(SalesInvoice)
class SalesInvoiceAdmin(ModelAdmin):
    list_display = (
        'invoice_number',
        'company',
        'customer',
        'branch',
        'warehouse',
        'date',
        'status',
        'total_amount',
    )

    list_filter = (
        'company',
        'status',
        'branch',
        'warehouse',
        'date',
    )

    search_fields = (
        'invoice_number',
        'customer__name',
        'notes',
    )

    ordering = ('-date', '-id')

    inlines = [SalesInvoiceItemInline]

    autocomplete_fields = ('company', 'branch', 'customer', 'warehouse')

    readonly_fields = (
        'invoice_number',
        'total_amount',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    actions = ['post_invoices']

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                'company',
                ('invoice_number', 'date'),
                ('branch', 'warehouse'),
                ('customer', 'status'),
            )
        }),
        ('التفاصيل المالية', {
            'fields': (
                'total_amount',
                'notes',
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

    @admin.action(description="ترحيل فواتير المبيعات المختارة")
    def post_invoices(self, request, queryset):
        posted_count = 0

        for invoice in queryset:
            if invoice.status != 'draft':
                self.message_user(
                    request,
                    f"تم تخطي الفاتورة {invoice.invoice_number}: ليست في حالة draft.",
                    level=messages.WARNING
                )
                continue

            try:
                SalesService.post_invoice(invoice)
                posted_count += 1
            except Exception as exc:
                self.message_user(
                    request,
                    f"فشل ترحيل الفاتورة {invoice.invoice_number}: {exc}",
                    level=messages.ERROR
                )

        if posted_count:
            self.message_user(
                request,
                f"تم ترحيل {posted_count} فاتورة مبيعات بنجاح.",
                level=messages.SUCCESS
            )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and obj.status == 'posted':
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status == 'posted':
            return False
        return super().has_delete_permission(request, obj)