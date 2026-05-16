from decimal import Decimal

from django.db import transaction

from apps.accounting.services.accounting_service import AccountingService
from apps.inventory.models import StockTransaction
from apps.inventory.services.stock_service import StockService


class SalesService:
    @staticmethod
    @transaction.atomic
    def post_invoice(invoice):
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

            StockService.post_transaction(stock_tx)

        journal_entry = AccountingService.create_sales_invoice_entry(invoice)
        invoice.journal_entry = journal_entry
        invoice.status = "posted"
        invoice.save(update_fields=["journal_entry", "status", "updated_at"])

        return stock_tx
