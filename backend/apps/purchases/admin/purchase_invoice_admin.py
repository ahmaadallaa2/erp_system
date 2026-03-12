# apps/purchases/admin.py

from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline

# استدعاء موديلات الفاتورة
from ..models.purchase_invoice import PurchaseInvoice
from ..models.purchase_invoice_item import PurchaseInvoiceItem

# استدعاء السيرفيس اللي هتشغل خوارزمية التكلفة
from ..services.inventory_services import InventorySyncService

# ==========================================
# 1. Inline Configuration for Purchase Invoice Items
# ==========================================
class PurchaseInvoiceItemInline(TabularInline):
    model = PurchaseInvoiceItem
    extra = 1 
    
    fields = ('product', 'quantity', 'unit_price', 'total_cost', 'notes')
    readonly_fields = ('total_cost',)

# ==========================================
# 2. Main Purchase Invoice Admin Configuration
# ==========================================
@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(ModelAdmin):
    list_display = (
        'invoice_number', 
        'supplier', 
        'branch', 
        'warehouse', 
        'invoice_date', 
        'status', 
        'total_amount'
    )
    
    list_filter = (
        'status', 
        'branch', 
        'warehouse', 
        'invoice_date'
    )
    
    search_fields = (
        'invoice_number', 
        'vendor_bill_number', 
        'supplier__name', 
        'notes'
    )
    
    inlines = [PurchaseInvoiceItemInline]
    
    # locking calculated and auto-generated fields to prevent manual tampering.
    readonly_fields = (
        'invoice_number', 
        'total_amount', 
        'created_at', 
        'updated_at'
    )
    
    ordering = ('-invoice_date', '-id')

    fieldsets = (
        ('البيانات الأساسية (Basic Information)', {
            'fields': (
                ('invoice_number', 'invoice_date'),
                ('branch', 'warehouse'),
                ('supplier', 'status')
            )
        }),
        # التعديل الأول: قسم خاص بالتكلفة الشاملة (Landed Costs)
        ('التكلفة الشاملة للمشتريات (Landed Costs)', {
            'fields': (
                ('shipping_cost', 'clearance_cost'),
                'commission_percentage',
            ),
            'description': 'أدخل المصاريف الإضافية هنا ليقوم النظام بتوزيعها على المنتجات وتحديث متوسط التكلفة تلقائياً.',
        }),
        ('الارتباطات والتفاصيل المالية (Links & Financials)', {
            'fields': (
                ('purchase_order', 'vendor_bill_number'),
                'total_amount',
                'notes'
            )
        }),
        ('سجلات النظام (System Records)', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            'classes': ('collapse',),
        }),
    )

    # التعديل الثاني: تنفيذ خوارزمية التكلفة عند التأكيد
    def save_model(self, request, obj, form, change):
        # نحفظ الفاتورة الأول عشان تاخد ID والمنتجات والـ Inlines تتحفظ
        super().save_model(request, obj, form, change)
        
        # لو المحاسب غير الحالة لـ "مؤكدة"، ننده على السيرفيس تحسب الليلة دي كلها
        if obj.status == 'confirmed':
            try:
                success, msg = InventorySyncService.process_purchase_invoice(obj)
                if success:
                    messages.success(request, msg)
                else:
                    messages.warning(request, f"تنبيه: {msg}")
            except Exception as e:
                messages.error(request, f"خطأ برمجي أثناء الترحيل: {str(e)}")