from django.contrib import admin, messages
from unfold.admin import ModelAdmin

from apps.accounting.models.payment import Payment
from apps.accounting.services.payment_service import PaymentService


@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = (
        'voucher_number',
        'company',
        'branch',
        'partner',
        'payment_type',
        'payment_method',
        'account',
        'amount',
        'date',
        'status',
        'has_journal_entry',
    )

    list_filter = (
        'company',
        'branch',
        'payment_type',
        'payment_method',
        'status',
        'date',
    )

    search_fields = (
        'voucher_number',
        'partner__name',
        'reference',
        'notes',
    )

    ordering = ('-date', '-id')

    autocomplete_fields = (
        'company',
        'branch',
        'partner',
        'account',
    )

    readonly_fields = (
        'voucher_number',
        'status',
        'journal_entry',
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

    actions = ('action_post_payments', 'action_cancel_payments')

    fieldsets = (
        ('بيانات السند الأساسية', {
            'fields': (
                'company',
                'branch',
                ('voucher_number', 'date'),
                ('payment_type', 'payment_method'),
                ('partner', 'account'),
                ('amount', 'status'),
            )
        }),
        ('معلومات إضافية', {
            'fields': (
                'reference',
                'notes',
                'cancellation_reason',
                'journal_entry',
            )
        }),
        ('سجلات النظام', {
            'classes': ('collapse',),
            'fields': (
                ('posted_by', 'posted_at'),
                ('cancelled_by', 'cancelled_at'),
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            )
        }),
    )

    @admin.display(description="مُرحل حسابياً؟", boolean=True)
    def has_journal_entry(self, obj):
        return bool(obj.journal_entry_id)

    @admin.action(description='ترحيل السندات المحددة')
    def action_post_payments(self, request, queryset):
        success_count = 0

        for payment in queryset:
            if payment.status != 'draft':
                self.message_user(
                    request,
                    f"تم تخطي السند {payment.voucher_number}: ليس في حالة draft.",
                    level=messages.WARNING
                )
                continue

            try:
                PaymentService.post_payment(payment, user=request.user)
                success_count += 1
            except Exception as e:
                self.message_user(
                    request,
                    f"فشل ترحيل السند {payment.voucher_number}: {str(e)}",
                    level=messages.ERROR
                )

        if success_count:
            self.message_user(
                request,
                f"تم ترحيل {success_count} سند بنجاح.",
                level=messages.SUCCESS
            )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description='Cancel selected payments')
    def action_cancel_payments(self, request, queryset):
        success_count = 0

        for payment in queryset:
            if payment.status != 'posted':
                self.message_user(
                    request,
                    f"Skipped payment {payment.voucher_number}: not in posted status.",
                    level=messages.WARNING
                )
                continue

            try:
                PaymentService.cancel_payment(payment, user=request.user)
                success_count += 1
            except Exception as exc:
                self.message_user(
                    request,
                    f"Failed to cancel payment {payment.voucher_number}: {exc}",
                    level=messages.ERROR
                )

        if success_count:
            self.message_user(
                request,
                f"Cancelled {success_count} payment(s) successfully.",
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
