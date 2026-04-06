from django.db import transaction

from apps.inventory.models import StockTransaction
from apps.inventory.services.stock_service import StockService


class PurchaseService:

    @staticmethod
    @transaction.atomic
    def post_invoice(invoice):
        """
        ترحيل فاتورة المشتريات:
        - إنشاء StockTransaction (IN)
        - إنشاء StockMovements
        - تحديث المخزون
        - تغيير حالة الفاتورة إلى posted
        """

        if invoice.status != 'draft':
            raise ValueError("Only draft invoices can be posted.")

        items = list(invoice.items.select_related('product'))
        if not items:
            raise ValueError("Cannot post an empty invoice.")

        # =====================================
        # 1. إنشاء StockTransaction
        # =====================================
        stock_tx = StockTransaction.objects.create(
            company=invoice.company,
            transaction_type='IN',
            source_warehouse=invoice.warehouse,
            date=invoice.invoice_date,
            reference=invoice.invoice_number,
            notes=f"Purchase Invoice: {invoice.invoice_number}"
        )

        # =====================================
        # 2. إنشاء الحركات (Movements)
        # =====================================
        for item in items:
            StockService.create_movement(
                transaction_obj=stock_tx,
                product=item.product,
                quantity=item.quantity,
                unit_cost=item.unit_price,
                note=f"From Purchase Invoice {invoice.invoice_number}"
            )

        # =====================================
        # 3. ترحيل الحركة (يحدث المخزون والتكلفة)
        # =====================================
        StockService.post_transaction(stock_tx)

        # =====================================
        # 4. تحديث حالة الفاتورة
        # =====================================
        invoice.status = 'posted'
        invoice.save(update_fields=['status', 'updated_at'])

        return stock_tx