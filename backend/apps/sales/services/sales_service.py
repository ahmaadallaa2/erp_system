from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.accounting.models import JournalEntry, JournalItem
from apps.accounting.services.accounting_service import AccountingService
from apps.inventory.models import StockTransaction
from apps.inventory.services.stock_service import StockService


class SalesService:
    @staticmethod
    @transaction.atomic
    def post_invoice(invoice, user=None):
        """
        ترحيل فاتورة المبيعات:
        - إنشاء StockTransaction (OUT) للأصناف المخزنية فقط
        - تجاهل الخدمات من الحركات المخزنية
        - خصم المخزون عبر StockService
        - تغيير حالة الفاتورة إلى posted
        """

        if invoice.status != "draft":
            raise ValueError("Only draft sales invoices can be posted.")

        items = list(invoice.items.select_related("product"))
        if not items:
            raise ValueError("Cannot post an empty sales invoice.")

        if invoice.total_amount <= Decimal("0.00"):
            raise ValueError("Invoice total must be greater than zero before posting.")

        stock_items = [
            item for item in items
            if item.product and item.product.product_type != "service"
        ]

        stock_tx = None

        # نعمل حركة مخزنية فقط لو فيه أصناف تحتاج صرف فعلي من المخزن
        if stock_items:
            if not invoice.warehouse_id:
                raise ValueError(
                    "Warehouse is required to post stock items in a sales invoice."
                )

            stock_tx = StockTransaction.objects.create(
                company=invoice.company,
                transaction_type="OUT",
                source_warehouse=invoice.warehouse,
                date=invoice.date,
                reference=invoice.invoice_number,
                notes=f"Sales Invoice: {invoice.invoice_number}",
            )

            for item in stock_items:
                product = item.product

                StockService.create_movement(
                    transaction_obj=stock_tx,
                    product=product,
                    quantity=item.quantity,
                    unit_cost=product.average_cost or Decimal("0.00"),
                    note=f"From Sales Invoice {invoice.invoice_number}",
                )

            StockService.post_transaction(stock_tx, user=user)

        journal_entry = AccountingService.create_sales_invoice_entry(invoice)
        invoice.journal_entry = journal_entry
        invoice.status = "posted"
        invoice.posted_by = user
        invoice.posted_at = timezone.now()
        invoice.save(
            update_fields=[
                "journal_entry",
                "status",
                "posted_by",
                "posted_at",
                "updated_at",
            ]
        )

        return stock_tx

    @staticmethod
    @transaction.atomic
    def cancel_invoice(invoice, user=None, reason=""):
        if invoice.status == "draft":
            raise ValueError("Draft sales invoices cannot be cancelled.")

        if invoice.status == "cancelled":
            raise ValueError("Sales invoice is already cancelled.")

        if invoice.status != "posted":
            raise ValueError("Only posted sales invoices can be cancelled.")

        if not invoice.journal_entry_id:
            raise ValueError("Posted sales invoice has no linked journal entry.")

        stock_items = [
            item for item in invoice.items.select_related("product")
            if item.product and item.product.product_type != "service"
        ]

        reversal_stock_tx = None
        if stock_items:
            original_stock_tx = SalesService._get_original_stock_transaction(invoice)
            reversal_stock_tx = SalesService._create_reversal_stock_transaction(
                invoice=invoice,
                original_stock_tx=original_stock_tx,
                user=user,
            )

        reversal_journal_entry = SalesService._create_reversal_journal_entry(invoice)

        invoice.status = "cancelled"
        invoice.cancelled_by = user
        invoice.cancelled_at = timezone.now()
        invoice.cancellation_reason = reason or ""
        invoice.save(
            update_fields=[
                "status",
                "cancelled_by",
                "cancelled_at",
                "cancellation_reason",
                "updated_at",
            ]
        )

        return {
            "stock_transaction": reversal_stock_tx,
            "journal_entry": reversal_journal_entry,
        }

    @staticmethod
    def _get_original_stock_transaction(invoice):
        stock_tx = (
            StockTransaction.objects
            .filter(
                company=invoice.company,
                transaction_type="OUT",
                status="posted",
                reference=invoice.invoice_number,
            )
            .prefetch_related("items__product")
            .order_by("-created_at")
            .first()
        )

        if not stock_tx:
            raise ValueError("Original posted stock transaction was not found.")

        return stock_tx

    @staticmethod
    def _create_reversal_stock_transaction(invoice, original_stock_tx, user=None):
        reversal_stock_tx = StockTransaction.objects.create(
            company=invoice.company,
            transaction_type="IN",
            source_warehouse=original_stock_tx.source_warehouse,
            date=timezone.now().date(),
            reference=f"REV-{invoice.invoice_number}",
            notes=(
                f"Reversal of Sales Invoice: {invoice.invoice_number}; "
                f"original stock transaction: {original_stock_tx.code}"
            ),
        )

        for original_item in original_stock_tx.items.select_related("product"):
            StockService.create_movement(
                transaction_obj=reversal_stock_tx,
                product=original_item.product,
                quantity=original_item.quantity,
                unit_cost=original_item.unit_cost,
                note=f"Reversal of Sales Invoice {invoice.invoice_number}",
            )

        StockService.post_transaction(reversal_stock_tx, user=user)
        return reversal_stock_tx

    @staticmethod
    def _create_reversal_journal_entry(invoice):
        original_entry = (
            JournalEntry.objects
            .select_related("journal", "company")
            .prefetch_related("items__account", "items__partner")
            .get(id=invoice.journal_entry_id)
        )

        if original_entry.status != "posted":
            raise ValueError("Only posted journal entries can be reversed.")

        reversal_entry = JournalEntry.objects.create(
            company=original_entry.company,
            journal=original_entry.journal,
            date=timezone.now().date(),
            reference=f"REV-{invoice.invoice_number}",
            notes=(
                f"Reversal of Sales Invoice {invoice.invoice_number}; "
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
