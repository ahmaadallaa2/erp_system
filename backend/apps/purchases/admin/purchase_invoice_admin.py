from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

# استدعاء موديلات الفاتورة الجديدة
from ..models.purchase_invoice import PurchaseInvoice
from ..models.purchase_invoice_item import PurchaseInvoiceItem

# ==========================================
# 1. Inline Configuration for Purchase Invoice Items
# ==========================================
# this class displays the invoice items as a table inside the parent invoice form.
class PurchaseInvoiceItemInline(TabularInline):
    model = PurchaseInvoiceItem
    extra = 1 
    
    fields = ('product', 'quantity', 'unit_price', 'total_cost', 'notes')
    
    # total_cost must be readonly because it is calculated automatically.
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
    
    # added vendor_bill_number here so the accountant can search by the physical paper bill number.
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