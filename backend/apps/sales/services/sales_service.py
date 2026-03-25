from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist
from apps.inventory.models import StockDocument
from apps.inventory.services.stock_service import StockService
from apps.accounting.models import Journal, JournalEntry, JournalItem, Account

class SalesService:
    @staticmethod
    def process_sales_invoice(invoice):
        """
        خدمة ترحيل فاتورة المبيعات:
        1. إنشاء إذن صرف مخزني (StockDocument).
        2. خصم الأصناف من المخزن عبر (StockService).
        3. إنشاء قيد محاسبي مزدوج (إيرادات + تكلفة بضاعة مباعة).
        4. الربط الكامل بين المستندات لضمان التتبع (Traceability).
        """

        # 1. التحقق من عدم الترحيل المسبق (Idempotency)
        if JournalEntry.objects.filter(reference=invoice.invoice_number).exists():
            return False, "هذه الفاتورة تم ترحيلها محاسبياً مسبقاً."

        if not invoice.items.exists():
            return False, "لا يمكن ترحيل فاتورة لا تحتوي على أصناف."

        with transaction.atomic():
            # ========================================================
            # 2. إنشاء "إذن الصرف" المخزني (الأب)
            # ========================================================
            try:
                stock_doc = StockDocument.objects.create(
                    document_type='OUT', # صادر / صرف
                    warehouse=invoice.warehouse,
                    reference=invoice.invoice_number,
                    notes=f"إذن صرف آلي للفاتورة رقم: {invoice.invoice_number}",
                    created_by=invoice.created_by
                )
            except Exception as e:
                return False, f"فشل في إنشاء إذن المخزن: {str(e)}"

            total_cogs = Decimal('0.00') # لتجميع تكلفة البضاعة المباعة

            # ========================================================
            # 3. معالجة الأصناف (مخازن + حساب تكلفة)
            # ========================================================
            for item in invoice.items.all():
                # أ. تسجيل حركة الصنف وتحديث الرصيد اللحظي
                try:
                    # نستخدم السيرفيس المركزية لضمان استخدام الـ F() وتجنب تضارب البيانات
                    StockService.register_movement(
                        document=stock_doc,
                        product=item.product,
                        quantity=item.quantity,
                        notes=f"مبيعات - فاتورة {invoice.invoice_number}"
                    )
                except Exception as e:
                    # في حالة فشل الصرف (مثل نقص الرصيد)، الترانزاكشن بالكامل ستتراجع
                    raise Exception(f"خطأ في صرف الصنف {item.product.name}: {str(e)}")

                # ب. حساب تكلفة الصنف بناءً على المتوسط المرجح (AVCO) المسجل في كارت الصنف
                # نستخدم average_cost وفي حالة عدم وجوده نستخدم سعر التكلفة الافتراضي
                unit_cost = item.product.average_cost or item.product.cost_price or Decimal('0.00')
                total_cogs += (item.quantity * unit_cost)

            # ========================================================
            # 4. الترحيل المحاسبي (قيد اليومية)
            # ========================================================
            # أ. تجهيز الحسابات والدفاتر
            try:
                journal = Journal.objects.get(code='SAL') # دفتر المبيعات
                sales_revenue_acc = Account.objects.get(code='4001') # حساب الإيرادات
                cogs_acc = Account.objects.get(code='5001')          # تكلفة البضاعة المباعة
                inventory_acc = Account.objects.get(code='1004')     # حساب المخزون (أصل)

                # تحديد الطرف المدين (خزينة للكاش / حساب العملاء للآجل)
                payment_type = getattr(invoice, 'payment_type', 'credit')
                if payment_type == 'cash':
                    if not invoice.treasury_account:
                        raise Exception("يجب تحديد حساب الخزينة للفاتورة النقدية.")
                    debit_account = invoice.treasury_account
                    partner_link = None
                    entry_desc = f"إثبات مبيعات نقدية - فاتورة {invoice.invoice_number}"
                else:
                    debit_account = Account.objects.get(code='1003') # حساب العملاء العام
                    partner_link = invoice.customer
                    entry_desc = f"إثبات مبيعات آجلة - عميل: {invoice.customer.name}"

            except ObjectDoesNotExist as e:
                raise Exception(f"فشل الترحيل: تأكد من إعداد شجرة الحسابات (أكواد: 4001, 5001, 1004, 1003). التفاصيل: {str(e)}")

            # ب. إنشاء رأس القيد
            journal_entry = JournalEntry.objects.create(
                journal=journal,
                date=invoice.date,
                reference=invoice.invoice_number,
                status='posted',
                notes=entry_desc,
                created_by=invoice.created_by
            )

            # ج. سطور القيد: (1) قيد الإيرادات بسعر البيع
            total_sales_amount = Decimal(str(invoice.total_amount))
            
            # الطرف المدين (العميل أو الخزينة)
            JournalItem.objects.create(
                entry=journal_entry,
                account=debit_account,
                partner=partner_link,
                debit=total_sales_amount,
                credit=0,
                description=entry_desc
            )
            # الطرف الدائن (حساب المبيعات)
            JournalItem.objects.create(
                entry=journal_entry,
                account=sales_revenue_acc,
                debit=0,
                credit=total_sales_amount,
                description="إيرادات مبيعات الفاتورة"
            )

            # د. سطور القيد: (2) قيد التكلفة (COGS)
            if total_cogs > 0:
                # الطرف المدين: مصروف تكلفة البضاعة المباعة
                JournalItem.objects.create(
                    entry=journal_entry,
                    account=cogs_acc,
                    debit=total_cogs,
                    credit=0,
                    description=f"تكلفة البضاعة المباعة للفاتورة {invoice.invoice_number}"
                )
                # الطرف الدائن: خفض قيمة المخزون (الأصل)
                JournalItem.objects.create(
                    entry=journal_entry,
                    account=inventory_acc,
                    debit=0,
                    credit=total_cogs,
                    description="تخفيض المخزون بسعر التكلفة"
                )

            # ========================================================
            # 5. الربط النهائي للتوثيق (The Magic Link)
            # ========================================================
            # نربط الإذن المخزني بالقيد المحاسبي الناتج عنه
            stock_doc.journal_entry = journal_entry
            stock_doc.save()

            return True, "تم ترحيل الفاتورة للمخازن والحسابات بنجاح."