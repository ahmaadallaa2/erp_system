from decimal import Decimal

from apps.inventory.models import StockMovement


class ProductMovementHistoryReportService:
    @staticmethod
    def rows(
        company,
        product=None,
        warehouse=None,
        start_date=None,
        end_date=None,
        transaction_type=None,
    ):
        queryset = (
            StockMovement.objects.filter(
                transaction__company=company,
                transaction__status="posted",
            )
            .select_related(
                "transaction",
                "transaction__source_warehouse",
                "transaction__destination_warehouse",
                "product",
            )
            .order_by("transaction__date", "transaction__code", "id")
        )

        if product:
            queryset = queryset.filter(product=product)

        if start_date:
            queryset = queryset.filter(transaction__date__gte=start_date)

        if end_date:
            queryset = queryset.filter(transaction__date__lte=end_date)

        if transaction_type:
            queryset = queryset.filter(transaction__transaction_type=transaction_type)

        rows = []
        for movement in queryset:
            rows.extend(
                ProductMovementHistoryReportService._movement_rows(
                    movement=movement,
                    warehouse=warehouse,
                )
            )

        return rows

    @staticmethod
    def _movement_rows(movement, warehouse=None):
        transaction = movement.transaction

        if transaction.transaction_type == "IN":
            return [
                ProductMovementHistoryReportService._build_row(
                    movement=movement,
                    warehouse_obj=transaction.source_warehouse,
                    quantity_in=movement.quantity,
                    quantity_out=Decimal("0.00"),
                )
            ] if ProductMovementHistoryReportService._matches_warehouse(
                transaction.source_warehouse,
                warehouse,
            ) else []

        if transaction.transaction_type == "OUT":
            return [
                ProductMovementHistoryReportService._build_row(
                    movement=movement,
                    warehouse_obj=transaction.source_warehouse,
                    quantity_in=Decimal("0.00"),
                    quantity_out=movement.quantity,
                )
            ] if ProductMovementHistoryReportService._matches_warehouse(
                transaction.source_warehouse,
                warehouse,
            ) else []

        if transaction.transaction_type == "TRANSFER":
            rows = []
            if ProductMovementHistoryReportService._matches_warehouse(
                transaction.source_warehouse,
                warehouse,
            ):
                rows.append(
                    ProductMovementHistoryReportService._build_row(
                        movement=movement,
                        warehouse_obj=transaction.source_warehouse,
                        quantity_in=Decimal("0.00"),
                        quantity_out=movement.quantity,
                    )
                )

            if ProductMovementHistoryReportService._matches_warehouse(
                transaction.destination_warehouse,
                warehouse,
            ):
                rows.append(
                    ProductMovementHistoryReportService._build_row(
                        movement=movement,
                        warehouse_obj=transaction.destination_warehouse,
                        quantity_in=movement.quantity,
                        quantity_out=Decimal("0.00"),
                    )
                )

            return rows

        return []

    @staticmethod
    def _matches_warehouse(warehouse_obj, warehouse):
        return warehouse is None or warehouse_obj == warehouse

    @staticmethod
    def _build_row(movement, warehouse_obj, quantity_in, quantity_out):
        transaction = movement.transaction

        return {
            "date": transaction.date,
            "transaction_id": transaction.id,
            "transaction_number": transaction.code,
            "reference": transaction.reference,
            "transaction_type": transaction.transaction_type,
            "product_id": movement.product_id,
            "product_name": movement.product.name,
            "warehouse_id": warehouse_obj.id,
            "warehouse_name": warehouse_obj.name,
            "quantity_in": quantity_in,
            "quantity_out": quantity_out,
            "unit_cost": movement.unit_cost,
            "notes": movement.note or transaction.notes or transaction.reference,
        }
