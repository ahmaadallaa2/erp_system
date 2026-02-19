from django.contrib import admin
from .models import Category, Unit, Product, Warehouse, Stock
from unfold.admin import ModelAdmin

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(Unit)
class UnitAdmin(ModelAdmin):
    list_display = ('name', 'short_name', 'created_at')
    search_fields = ('name', 'short_name')

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'sku', 'category', 'unit', 'sale_price', 'product_type', 'is_active')
    list_filter = ('category', 'product_type', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'barcode', 'description')
    ordering = ('name',)
    
    # حقل SKU للقراءة فقط لأنه بيتولد أوتوماتيك
    readonly_fields = ('sku', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات أساسية', {
            'fields': ('name', 'sku', 'product_type', 'barcode', 'is_active')
        }),
        ('التصنيف والوحدة', {
            'fields': ('category', 'unit')
        }),
        ('التسعير', {
            'fields': ('cost_price', 'sale_price')
        }),
        ('تفاصيل أخرى', {
            'fields': ('description', 'image')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )
@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ('name', 'branch', 'keeper', 'is_active')
    list_filter = ('branch', 'is_active')
    search_fields = ('name', 'branch__name', 'keeper__full_name')

@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity', 'location')
    list_filter = ('warehouse', 'product__category')
    search_fields = ('product__name', 'product__sku')
    
    # يفضل جعل الكمية للقراءة فقط هنا، لأننا هنعدلها بحركات رسمية لاحقاً
    readonly_fields = ('quantity',)

