from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from apps.inventory.models import StockBalance, StockMovement


class StockService:
    @staticmethod
    def create_movement(transaction_obj, product, quantity, unit_cost=None, note=None):
        """
        إنشاء سطر حركة مخزنية أثناء كون المستند Draft فقط.
        """
        if transaction_obj.status != 'draft':
            raise ValueError("Cannot add items to a non-draft transaction.")

        return StockMovement.objects.create(
            transaction=transaction_obj,
            product=product,
            quantity=quantity,
            unit_cost=unit_cost if unit_cost is not None else Decimal("0.00"),
            note=note
        )

    @staticmethod
    @transaction.atomic
    def post_transaction(transaction_obj):
        """
        ترحيل حركة مخزنية:
        - تحديث StockBalance
        - تحديث average_cost في حالة الوارد
        - منع الصرف/التحويل عند عدم كفاية الرصيد
        - تغيير الحالة إلى posted
        """
        if transaction_obj.status != 'draft':
            raise ValueError("Only draft transactions can be posted.")

        items = list(transaction_obj.items.select_related('product'))
        if not items:
            raise ValueError("Cannot post an empty stock transaction.")

        tx_type = transaction_obj.transaction_type
        company = transaction_obj.company
        source_warehouse = transaction_obj.source_warehouse
        destination_warehouse = transaction_obj.destination_warehouse

        for item in items:
            product = item.product
            quantity = item.quantity
            unit_cost = item.unit_cost or Decimal("0.00")

            if tx_type == 'IN':
                balance, _ = StockBalance.objects.select_for_update().get_or_create(
                    company=company,
                    product=product,
                    warehouse=source_warehouse,
                    defaults={
                        'quantity': Decimal("0.00"),
                        'reserved_quantity': Decimal("0.00"),
                    }
                )

                balance.quantity += quantity
                balance.save(update_fields=['quantity', 'updated_at'])

                if unit_cost > 0:
                    StockService._update_average_cost_on_in(product, quantity, unit_cost)

            elif tx_type == 'OUT':
                balance, _ = StockBalance.objects.select_for_update().get_or_create(
                    company=company,
                    product=product,
                    warehouse=source_warehouse,
                    defaults={
                        'quantity': Decimal("0.00"),
                        'reserved_quantity': Decimal("0.00"),
                    }
                )

                available_qty = balance.quantity - balance.reserved_quantity
                if available_qty < quantity:
                    raise ValueError(
                        f"Insufficient stock for product '{product}'. "
                        f"Available: {available_qty}, Required: {quantity}"
                    )

                balance.quantity -= quantity
                balance.save(update_fields=['quantity', 'updated_at'])

            elif tx_type == 'TRANSFER':
                if not destination_warehouse:
                    raise ValueError("Destination warehouse is required for transfer transactions.")

                source_balance, _ = StockBalance.objects.select_for_update().get_or_create(
                    company=company,
                    product=product,
                    warehouse=source_warehouse,
                    defaults={
                        'quantity': Decimal("0.00"),
                        'reserved_quantity': Decimal("0.00"),
                    }
                )

                available_qty = source_balance.quantity - source_balance.reserved_quantity
                if available_qty < quantity:
                    raise ValueError(
                        f"Insufficient stock for product '{product}' in source warehouse. "
                        f"Available: {available_qty}, Required: {quantity}"
                    )

                destination_balance, _ = StockBalance.objects.select_for_update().get_or_create(
                    company=company,
                    product=product,
                    warehouse=destination_warehouse,
                    defaults={
                        'quantity': Decimal("0.00"),
                        'reserved_quantity': Decimal("0.00"),
                    }
                )

                source_balance.quantity -= quantity
                destination_balance.quantity += quantity

                source_balance.save(update_fields=['quantity', 'updated_at'])
                destination_balance.save(update_fields=['quantity', 'updated_at'])

            else:
                raise ValueError(f"Unsupported transaction type: {tx_type}")

        transaction_obj.status = 'posted'
        transaction_obj.save(update_fields=['status', 'updated_at'])

        return transaction_obj

    @staticmethod
    def _update_average_cost_on_in(product, incoming_qty, incoming_unit_cost):
        """
        تحديث متوسط التكلفة المرجح عند الحركات الواردة فقط.
        """
        incoming_qty = Decimal(incoming_qty)
        incoming_unit_cost = Decimal(incoming_unit_cost)

        total_qty = (
            StockBalance.objects.filter(product=product, company=product.company)
            .aggregate(total=Sum('quantity'))
            .get('total')
            or Decimal("0.00")
        )

        old_total_qty = total_qty - incoming_qty
        old_avg_cost = product.average_cost or Decimal("0.00")

        if total_qty <= 0:
            product.average_cost = incoming_unit_cost
        else:
            old_total_value = old_total_qty * old_avg_cost
            new_total_value = incoming_qty * incoming_unit_cost
            product.average_cost = (old_total_value + new_total_value) / total_qty

        product.save(update_fields=['average_cost', 'updated_at'])