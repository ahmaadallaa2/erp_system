# apps/sales/admin.py

from django.contrib import admin, messages
from unfold.admin import ModelAdmin, TabularInline
from .models.sales_invoice import SalesInvoice, SalesInvoiceItem
from .services.sales_service import SalesService

class SalesInvoiceItemInline(TabularInline):
    model = SalesInvoiceItem
    extra = 1
    fields = ('product', 'quantity', 'unit_price', 'total_price')
    readonly_fields = ('total_price',)

@admin.register(SalesInvoice)
class SalesInvoiceAdmin(ModelAdmin):
    # 1. التعديل هنا: إضافة 'warehouse' للجدول الخارجي
    list_display = ('invoice_number', 'customer', 'warehouse', 'date', 'total_amount', 'status')
    
    # 2. التعديل هنا: إضافة 'warehouse' للفلاتر الجانبية
    list_filter = ('status', 'warehouse', 'date')
    
    search_fields = ('invoice_number', 'customer__name')
    inlines = [SalesInvoiceItemInline]
    autocomplete_fields = ('customer',)
    
    # الحقول اللي السيستم بيكريتها أوتوماتيك
    readonly_fields = ('invoice_number', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                ('customer', 'date'),
                ('warehouse', 'status'), # 3. التعديل هنا: حطينا المخزن والحالة في سطر واحد
                'notes'
            )
        }),
        ('سجلات النظام', {
            'fields': (
                'invoice_number',
                ('created_at', 'updated_at'), 
                ('created_by', 'updated_by')
            ),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        # نحفظ الفاتورة الأول عشان تاخد ID والمنتجات تتحفظ
        super().save_model(request, obj, form, change)
        
        # لو المحاسب غير الحالة لـ "مؤكدة"، ننده على السيرفيس ترحل الشغل
        if obj.status == 'confirmed':
            try:
                success, msg = SalesService.process_sales_invoice(obj)
                if success:
                    messages.success(request, msg)
                else:
                    messages.warning(request, f"تنبيه: {msg}")
            except Exception as e:
                messages.error(request, f"خطأ برمجي أثناء الترحيل: {str(e)}")