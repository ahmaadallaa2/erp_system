from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import (
    Category,
    Unit,
    Product,
    Warehouse,
    Stock,
    StockMovement
)

# ==========================================
# 1. الأساسيات والتصنيفات (Lookup Tables)
# ==========================================

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'created_at')
    list_filter = ('parent',)
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(Unit)
class UnitAdmin(ModelAdmin):
    list_display = ('name', 'short_name', 'created_at')
    search_fields = ('name', 'short_name')
    ordering = ('name',)


# ==========================================
# 2. المنتجات والمخازن (Master Data)
# ==========================================

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'sku', 'category', 'unit', 'sale_price', 'average_cost', 'product_type', 'is_active')
    list_filter = ('category', 'product_type', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'barcode', 'description')
    ordering = ('name',)
    
    # حقل SKU ومتوسط التكلفة للقراءة فقط (التكلفة تُحسب آلياً من المشتريات)
    readonly_fields = ('sku', 'average_cost', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات أساسية', {
            'fields': ('company', 'name', 'sku', 'product_type', 'barcode', 'is_active')
        }),
        ('التصنيف والوحدة', {
            'fields': ('category', 'unit')
        }),
        ('التسعير والتكلفة', {
            'fields': ('cost_price', 'average_cost', 'sale_price')
        }),
        ('إدارة المخزون وتفاصيل أخرى', {
            'fields': ('reorder_point', 'description')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )


@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    # 1. عرض الأعمدة في القائمة الرئيسية (ضفنا الكود في البداية)
    list_display = ('code', 'name', 'branch', 'keeper', 'is_active')
    
    # 2. الفلاتر الجانبية
    list_filter = ('branch', 'is_active')
    
    # 3. حقول البحث (بحث بالكود، الاسم، اسم الفرع، أو اسم الأمين)
    search_fields = ('code', 'name', 'branch__name', 'keeper__first_name', 'keeper__last_name')
    
    # 4. الترتيب الافتراضي (يفضل الترتيب بالكود أو الاسم)
    ordering = ('code', 'name')
    
    # 5. الحقول غير القابلة للتعديل (الكود وحقول النظام)
    readonly_fields = ('code', 'created_at', 'updated_at', 'created_by', 'updated_by')

    # 6. تقسيم صفحة الإضافة/التعديل بشكل مريح للعين (Fieldsets)
    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'code', 'is_active')
        }),
        ('الإدارة والموقع', {
            'fields': ('branch', 'address', 'keeper')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

# ==========================================
# 3. الأرصدة وحركات المخزون (Inventory & Transactions)
# ==========================================

@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity', 'location')
    list_filter = ('warehouse', 'product__category')
    search_fields = ('product__name', 'product__sku')
    ordering = ('warehouse', 'product')
    
    # الرصيد يتم تعديله فقط عبر حركات المخزون الرسمية
    readonly_fields = ('quantity',)

    fieldsets = (
        ('بيانات التخزين', {
            'fields': ('product', 'warehouse', 'location')
        }),
        ('الأرصدة', {
            'fields': ('quantity',)
        }),
    )


@admin.register(StockMovement)
class StockMovementAdmin(ModelAdmin):
    list_display = ('id', 'product', 'warehouse', 'movement_type', 'quantity', 'created_at', 'created_by')
    list_filter = ('movement_type', 'warehouse', 'created_at', 'product__category')
    search_fields = ('product__name', 'reference', 'notes')
    ordering = ('-created_at',)
    
    readonly_fields = ('created_at',)

    fieldsets = (
        ('بيانات الحركة الأساسية', {
            'fields': ('product', 'warehouse', 'movement_type', 'quantity')
        }),
        ('التوثيق والارتباطات', {
            'fields': ('reference', 'notes', 'created_by')
        }),
    )

    def has_change_permission(self, request, obj=None):
        """
        منع تعديل الحركة المخزنية بعد إنشائها للحفاظ على دقة الأرصدة
        """
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)