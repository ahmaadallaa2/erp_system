from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.accounting.models import JournalEntry, JournalItem
from apps.accounting.services.accounting_service import AccountingService


class PaymentService:
    @staticmethod
    @transaction.atomic
    def post_payment(payment, user=None):
        """
        ترحيل السند المالي:
        - إنشاء القيد المحاسبي عبر AccountingService
        - ربطه بالسند
        - تحديث حالة السند إلى posted
        """

        if payment.status != 'draft':
            raise ValidationError("يمكن ترحيل السندات المالية من حالة draft فقط.")

        if payment.journal_entry_id:
            raise ValidationError("يوجد قيد يومية مرتبط بهذا السند بالفعل.")

        entry = AccountingService.create_payment_journal_entry(payment)

        payment.journal_entry = entry
        payment.status = 'posted'
        payment.posted_by = user
        payment.posted_at = timezone.now()
        payment.save(
            update_fields=[
                'journal_entry',
                'status',
                'posted_by',
                'posted_at',
                'updated_at',
            ]
        )

        return entry

    @staticmethod
    @transaction.atomic
    def cancel_payment(payment, user=None, reason=""):
        if payment.status == "draft":
            raise ValidationError("Draft payments cannot be cancelled.")

        if payment.status == "cancelled":
            raise ValidationError("Payment is already cancelled.")

        if payment.status != "posted":
            raise ValidationError("Only posted payments can be cancelled.")

        if not payment.journal_entry_id:
            raise ValidationError("Posted payment has no linked journal entry.")

        reversal_entry = PaymentService._create_reversal_journal_entry(payment)

        payment.status = "cancelled"
        payment.cancelled_by = user
        payment.cancelled_at = timezone.now()
        payment.cancellation_reason = reason or ""
        payment.save(
            update_fields=[
                "status",
                "cancelled_by",
                "cancelled_at",
                "cancellation_reason",
                "updated_at",
            ]
        )

        return reversal_entry

    @staticmethod
    def _create_reversal_journal_entry(payment):
        original_entry = (
            JournalEntry.objects
            .select_related("journal", "company")
            .prefetch_related("items__account", "items__partner")
            .get(id=payment.journal_entry_id)
        )

        if original_entry.status != "posted":
            raise ValidationError("Only posted journal entries can be reversed.")

        reversal_entry = JournalEntry.objects.create(
            company=original_entry.company,
            journal=original_entry.journal,
            date=timezone.now().date(),
            reference=f"REV-{payment.voucher_number}",
            notes=(
                f"Reversal of Payment {payment.voucher_number}; "
                f"original journal entry: {original_entry.entry_number}"
            ),
        )

        for original_item in original_entry.items.select_related("account", "partner"):
            JournalItem.objects.create(
                entry=reversal_entry,
                account=original_item.account,
                partner=original_item.partner,
                description=f"Reversal: {original_item.description}",
                debit=original_item.credit,
                credit=original_item.debit,
            )

        reversal_entry.post()
        return reversal_entry
