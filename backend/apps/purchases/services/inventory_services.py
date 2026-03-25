from django.db import transaction
from decimal import Decimal
from apps.inventory.models import StockDocument, StockMovement
from apps.inventory.services.stock_service import StockService
from apps.accounting.services import AccountingService

class InventorySyncService:
    
    @staticmethod
    def process_purchase_receipt(invoice):
        with transaction.atomic():
            # 1. Idempotency Check: التأكد من عدم تكرار العملية
            # بنشيك في أذونات المخازن عن طريق المرجع (رقم الفاتورة)
            if StockDocument.objects.filter(reference=invoice.invoice_number).exists():
                return False, "تم إدخال هذه الفاتورة للمخزن مسبقاً."
            
            # ========================================================
            # 2. إنشاء "إذن الإضافة" (الأب) قبل الدخول في الأصناف
            # ========================================================
            stock_doc = StockDocument.objects.create(
                document_type='IN', # وارد
                warehouse=invoice.warehouse,
                reference=invoice.invoice_number,
                notes=f"وارد مشتريات تلقائي من فاتورة رقم: {invoice.invoice_number}",
                # لو عندك created_by في الـ invoice ممكن تباصيها هنا
            )

            # --- حسابات التكلفة الشاملة (نفس اللوجيك العبقري بتاعك) ---
            total_items_value = sum(item.quantity * item.unit_price for item in invoice.items.all())
            
            shipping = Decimal(str(getattr(invoice, 'shipping_cost', 0)))
            clearance = Decimal(str(getattr(invoice, 'clearance_cost', 0)))
            commission_pct = Decimal(str(getattr(invoice, 'commission_percentage', 0)))
            
            commission_value = total_items_value * (commission_pct / Decimal('100.00'))
            total_additional_costs = shipping + clearance + commission_value
            # ========================================================

            # 3. المرور على عناصر الفاتورة وإرسالها لخدمة المخازن
            for item in invoice.items.all():
                
                # حساب نصيب القطعة من المصاريف (الوزن النسبي)
                item_value = item.quantity * item.unit_price
                weight_ratio = item_value / total_items_value if total_items_value > Decimal('0') else Decimal('0')
                item_share_of_costs = total_additional_costs * weight_ratio
                
                # التكلفة الشاملة النهائية للقطعة
                landed_unit_cost = item.unit_price + (item_share_of_costs / item.quantity)

                # ✅ استدعاء خدمة المخازن (بالتوقيع الجديد)
                StockService.register_movement(
                    document=stock_doc,  # بعتنا "الأب" اللي كريتناه فوق
                    product=item.product,
                    quantity=item.quantity,
                    unit_price=landed_unit_cost, # التكلفة اللي هيتحسب عليها المتوسط (AVCO)
                    notes=f"صنف: {item.product.name} من فاتورة {invoice.invoice_number}"
                )
                
            # 4. الترحيل المحاسبي (قيد المشتريات)
            # بنربط القيد بالإذن المخزني عشان المحاسب يعرف يوصلهم ببعض
            success, message, entry = AccountingService.create_purchase_invoice_entry(invoice)
            if not success:
                raise Exception(message)
            
            # ربط القيد بالإذن المخزني للتوثيق الكامل
            stock_doc.journal_entry = entry
            stock_doc.save()
                    
            return True, "تم حساب التكلفة الشاملة وتحديث المخزون والترحيل المحاسبي بنجاح."