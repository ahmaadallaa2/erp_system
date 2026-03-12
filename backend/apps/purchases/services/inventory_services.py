from django.db import transaction
from decimal import Decimal
from apps.inventory.models import StockMovement
from apps.inventory.services.stock_service import StockService
from apps.accounting.services import AccountingService

class InventorySyncService:
    
    @staticmethod
    def process_purchase_receipt(invoice):
        with transaction.atomic():
            # 1. Idempotency Check: التأكد من عدم تكرار الفاتورة
            movement_exists = StockMovement.objects.filter(reference=invoice.invoice_number).exists()
            if movement_exists:
                return False, "تم إدخال هذه الفاتورة للمخزن مسبقاً."
            
            # ========================================================
            # 2. خوارزمية التكلفة الشاملة (Landed Cost Calculation)
            # ========================================================
            # أ. حساب إجمالي قيمة البضاعة الأساسية من المصنع
            total_items_value = sum(item.quantity * item.unit_price for item in invoice.items.all())
            
            # ب. حساب إجمالي المصاريف الإضافية (شحن + أرضيات + عمولة)
            # بنستخدم getattr تحسباً لو الحقول لسه متعملهاش Migrate
            shipping = Decimal(str(getattr(invoice, 'shipping_cost', 0)))
            clearance = Decimal(str(getattr(invoice, 'clearance_cost', 0)))
            commission_pct = Decimal(str(getattr(invoice, 'commission_percentage', 0)))
            
            # حساب قيمة العمولة كنسبة من البضاعة
            commission_value = total_items_value * (commission_pct / Decimal('100.00'))
            
            # إجمالي التكاليف اللي هتتوزع
            total_additional_costs = shipping + clearance + commission_value
            # ========================================================

            # 3. المرور على عناصر الفاتورة وإرسالها لخدمة المخازن
            for item in invoice.items.all():
                
                # --- توزيع المصاريف على القطعة الواحدة (الوزن النسبي) ---
                item_value = item.quantity * item.unit_price
                
                # تجنب القسمة على صفر (كل الأرقام هنا Decimal)
                weight_ratio = item_value / total_items_value if total_items_value > Decimal('0') else Decimal('0')
                
                # نصيب الصنف ده من المصاريف الإضافية
                item_share_of_costs = total_additional_costs * weight_ratio
                
                # التكلفة الشاملة للقطعة الواحدة (Landed Unit Cost)
                landed_unit_cost = item.unit_price + (item_share_of_costs / item.quantity)
                # --------------------------------------------------------

                # السحر الحلال هنا: استدعاء خدمة المخازن المركزية
                StockService.register_movement(
                    product=item.product,
                    warehouse=invoice.warehouse,
                    movement_type='IN', # وارد
                    quantity=item.quantity,
                    reference=invoice.invoice_number,
                    notes=f"وارد مشتريات تلقائي من فاتورة رقم: {invoice.invoice_number}",
                    
                    # ✅ التعديل الأهم: بنبعت "التكلفة الشاملة" بدل السعر المجرد 
                    # عشان الـ StockService تحسب المتوسط المرجح (AVCO) على النظافة
                    unit_price=landed_unit_cost 
                )
                
            # 4. الترحيل المحاسبي (قيد المشتريات)
            success, message = AccountingService.create_purchase_invoice_entry(invoice)
            if not success:
                # لو المحاسبة ضربت إيرور، بنوقع الترانزاكشن كلها (المخزن هيرجع زي ما كان)
                raise Exception(message)
                    
            return True, "تم حساب التكلفة الشاملة وتحديث المخزون والترحيل المحاسبي بنجاح."