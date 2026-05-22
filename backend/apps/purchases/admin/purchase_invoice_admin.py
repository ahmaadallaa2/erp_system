from django.contrib import admin
from django.contrib import messages
from unfold.admin import ModelAdmin, TabularInline

from ..models.purchase_invoice import PurchaseInvoice
from ..models.purchase_invoice_item import PurchaseInvoiceItem
from ..services.purchase_service import PurchaseService


# ==========================================
# 1. Inline Configuration for Purchase Invoice Items
# ==========================================
class PurchaseInvoiceItemInline(TabularInline):
    model = PurchaseInvoiceItem
    extra = 1

    fields = ('product', 'quantity', 'unit_price', 'line_total', 'notes')
    readonly_fields = ('line_total',)
    autocomplete_fields = ('product',)

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_add_permission(request, obj)


# ==========================================
# 2. Main Purchase Invoice Admin Configuration
# ==========================================
@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(ModelAdmin):
    list_display = (
        'invoice_number',
        'company',
        'supplier',
        'branch',
        'warehouse',
        'invoice_date',
        'status',
        'total_amount',
    )

    list_filter = (
        'company',
        'status',
        'branch',
        'warehouse',
        'invoice_date',
    )

    search_fields = (
        'invoice_number',
        'vendor_bill_number',
        'supplier__name',
        'notes',
    )

    ordering = ('-invoice_date', '-id')

    inlines = [PurchaseInvoiceItemInline]

    autocomplete_fields = ('company', 'branch', 'supplier', 'warehouse')

    readonly_fields = (
        'invoice_number',
        'status',
        'total_amount',
        'posted_by',
        'posted_at',
        'cancelled_by',
        'cancelled_at',
        'cancellation_reason',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    actions = ['post_invoices', 'cancel_invoices']

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                'company',
                ('invoice_number', 'invoice_date'),
                ('branch', 'warehouse'),
                'supplier',
                'status',
            )
        }),
        ('التكلفة الشاملة للمشتريات', {
            'fields': (
                ('shipping_cost', 'clearance_cost'),
                'commission_percentage',
            ),
            'description': 'المصاريف الإضافية يمكن استخدامها لاحقًا في توزيع التكلفة الفعلية على الأصناف.',
        }),
        ('التفاصيل المالية والمرجعية', {
            'fields': (
                'vendor_bill_number',
                'total_amount',
                'cancellation_reason',
                'notes',
            )
        }),
        ('سجلات النظام', {
            'fields': (
                ('posted_by', 'posted_at'),
                ('cancelled_by', 'cancelled_at'),
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description="ترحيل فواتير المشتريات المختارة")
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
                PurchaseService.post_invoice(invoice, user=request.user)
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
                f"تم ترحيل {posted_count} فاتورة مشتريات بنجاح.",
                level=messages.SUCCESS
            )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description="Cancel selected purchase invoices")
    def cancel_invoices(self, request, queryset):
        cancelled_count = 0

        for invoice in queryset:
            if invoice.status != 'posted':
                self.message_user(
                    request,
                    f"Skipped invoice {invoice.invoice_number}: not in posted status.",
                    level=messages.WARNING
                )
                continue

            try:
                PurchaseService.cancel_invoice(invoice, user=request.user)
                cancelled_count += 1
            except Exception as exc:
                self.message_user(
                    request,
                    f"Failed to cancel invoice {invoice.invoice_number}: {exc}",
                    level=messages.ERROR
                )

        if cancelled_count:
            self.message_user(
                request,
                f"Cancelled {cancelled_count} purchase invoice(s) successfully.",
                level=messages.SUCCESS
            )

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions
