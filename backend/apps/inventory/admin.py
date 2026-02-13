from django.contrib import admin
from .models import Category, Unit, Product

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    search_fields = ('name',)
    list_filter = ('parent',)

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ('name', 'short_name', 'created_at')
    search_fields = ('name', 'short_name')

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
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