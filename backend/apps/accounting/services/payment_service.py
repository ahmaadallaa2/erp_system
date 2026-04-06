from django.db import transaction
from django.core.exceptions import ValidationError

from apps.accounting.services.accounting_service import AccountingService


class PaymentService:
    @staticmethod
    @transaction.atomic
    def post_payment(payment):
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
        payment.save(update_fields=['journal_entry', 'status', 'updated_at'])

        return entry