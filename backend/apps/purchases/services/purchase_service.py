from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction

from apps.accounting.services.accounting_service import AccountingService
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

        invoice.total_amount = PurchaseService._calculate_invoice_total(items, invoice)
        invoice.save(update_fields=['total_amount', 'updated_at'])
        allocated_unit_costs = PurchaseService._allocated_unit_costs(items, invoice.total_amount)
        allocated_stock_value = PurchaseService._stock_value_from_allocated_costs(
            items,
            allocated_unit_costs,
        )
        if allocated_stock_value != invoice.total_amount:
            raise ValueError(
                "Purchase landed costs cannot be allocated exactly with two-decimal unit costs."
            )

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
                unit_cost=allocated_unit_costs[item.id],
                note=f"From Purchase Invoice {invoice.invoice_number}"
            )

        # =====================================
        # 3. ترحيل الحركة (يحدث المخزون والتكلفة)
        # =====================================
        StockService.post_transaction(stock_tx)

        # =====================================
        # 4. تحديث حالة الفاتورة
        # =====================================
        journal_entry = AccountingService.create_purchase_invoice_entry(invoice)
        invoice.journal_entry = journal_entry
        invoice.status = 'posted'
        invoice.save(update_fields=['journal_entry', 'status', 'updated_at'])

        return stock_tx

    @staticmethod
    def _calculate_invoice_total(items, invoice):
        total = sum(
            (item.line_total or Decimal("0.00"))
            for item in items
        )
        total += invoice.shipping_cost or Decimal("0.00")
        total += invoice.clearance_cost or Decimal("0.00")

        return Decimal(total).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _allocated_unit_costs(items, invoice_total):
        line_total = sum(
            (item.line_total or Decimal("0.00"))
            for item in items
        )
        extra_cost = Decimal(invoice_total or Decimal("0.00")) - line_total

        if extra_cost <= Decimal("0.00") or line_total <= Decimal("0.00"):
            return {item.id: item.unit_price for item in items}

        allocated_costs = {}
        allocated_extra = Decimal("0.00")

        for index, item in enumerate(items):
            is_last = index == len(items) - 1
            if is_last:
                item_extra = extra_cost - allocated_extra
            else:
                item_extra = (
                    extra_cost
                    * (item.line_total or Decimal("0.00"))
                    / line_total
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                allocated_extra += item_extra

            line_value = (item.line_total or Decimal("0.00")) + item_extra
            allocated_costs[item.id] = (
                line_value / item.quantity
            ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        return allocated_costs

    @staticmethod
    def _stock_value_from_allocated_costs(items, allocated_unit_costs):
        stock_value = sum(
            item.quantity * allocated_unit_costs[item.id]
            for item in items
        )
        return Decimal(stock_value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
