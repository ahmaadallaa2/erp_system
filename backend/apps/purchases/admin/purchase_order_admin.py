from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from ..models import PurchaseOrder, PurchaseOrderItem

# ==========================================
# 1. Inline Configuration for Purchase Items
# ==========================================
# this class is used to display the purchase order items as a table inside the parent purchase order form.
class PurchaseOrderItemInline(TabularInline):
    model = PurchaseOrderItem
    
    # extra defines the number of empty rows displayed by default for adding new products.
    extra = 1 
    
    # these are the columns that will appear in the inline table.
    fields = ('product', 'quantity', 'unit_price', 'total_cost', 'notes')
    
    # total_cost must be readonly because it is calculated automatically in the model's save method.
    readonly_fields = ('total_cost',)


# ==========================================
# 2. Main Purchase Order Admin Configuration
# ==========================================
@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(ModelAdmin):
    # this defines the columns that will be displayed in the main list view of purchase orders.
    list_display = (
        'po_number', 
        'supplier', 
        'branch', 
        'warehouse', 
        'order_date', 
        'status', 
        'total_amount'
    )
    
    # this creates a sidebar filter to easily filter purchase orders by status, branch, or dates.
    list_filter = (
        'status', 
        'branch', 
        'warehouse', 
        'order_date'
    )
    
    # this adds a search bar to search for a specific order by its number or the supplier's name.
    search_fields = (
        'po_number', 
        'supplier__name', 
        'notes'
    )
    
    # this links the inline items table to the main purchase order form.
    inlines = [PurchaseOrderItemInline]
    
    # these fields are generated or calculated by the system and should not be editable by the user.
    readonly_fields = (
        'po_number', 
        'total_amount', 
        'created_at', 
        'updated_at'
    )
    
    # ordering the list view to show the newest orders first.
    ordering = ('-order_date', '-id')

    # fieldsets are used to organize the form fields into logical, clean sections for a better UI/UX experience.
    fieldsets = (
        ('البيانات الأساسية (Basic Information)', {
            'fields': (
                ('po_number', 'order_date'),
                ('branch', 'warehouse'),
                ('supplier', 'status')
            )
        }),
        ('التفاصيل المالية والإضافية (Financial & Additional Details)', {
            'fields': (
                'delivery_date',
                'total_amount',
                'notes'
            )
        }),
        ('سجلات النظام (System Records)', {
            'fields': (
                ('created_at', 'updated_at'),
            ),
            # 'collapse' makes this section hidden by default to keep the form clean.
            'classes': ('collapse',),
        }),
    )