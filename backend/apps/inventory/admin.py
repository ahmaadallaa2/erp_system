from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Category,
    Unit,
    Product,
    Warehouse,
    Stock,
    StockDocument,
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
    list_display = ('name', 'sku', 'category', 'sale_price', 'average_cost', 'product_type', 'is_active')
    list_filter = ('category', 'product_type', 'is_active', 'created_at', 'company')
    search_fields = ('name', 'sku', 'barcode', 'description')
    ordering = ('company', 'name')
    
    # تحسين الأداء: الدروب داون هيتحول لبحث AJAX سريع
    autocomplete_fields = ('company', 'category', 'unit', 'income_account', 'expense_account')
    
    # حقول للقراءة فقط (التكلفة تُحسب آلياً من المشتريات)
    readonly_fields = ('sku', 'average_cost', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات أساسية', {
            'fields': ('company', 'name', 'sku', 'product_type', 'barcode', 'image', 'is_active')
        }),
        ('التصنيف والوحدة', {
            'fields': ('category', 'unit')
        }),
        ('التسعير والتكلفة', {
            'fields': ('cost_price', 'average_cost', 'sale_price')
        }),
        ('الربط المحاسبي (ERP)', {
            'fields': ('income_account', 'expense_account'),
            'description': 'اتركها فارغة إذا كنت تريد استخدام الحسابات الافتراضية للتصنيف.'
        }),
        ('إدارة المخزون وتفاصيل أخرى', {
            'fields': ('reorder_point', 'description')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        """تسجيل المستخدم الذي قام بالإضافة أو التعديل آلياً"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ('code', 'name', 'warehouse_type', 'branch', 'keeper', 'is_active')
    list_filter = ('warehouse_type', 'branch', 'is_active')
    search_fields = ('code', 'name', 'branch__name', 'keeper__first_name', 'keeper__last_name')
    ordering = ('code', 'name')
    
    autocomplete_fields = ('branch', 'keeper')
    readonly_fields = ('code', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'code', 'warehouse_type', 'is_active')
        }),
        ('الإدارة والموقع', {
            'fields': ('branch', 'address', 'keeper')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ==========================================
# 3. الأرصدة (رصيد المخزن اللحظي)
# ==========================================

@admin.register(Stock)
class StockAdmin(ModelAdmin):
    list_display = ('product', 'warehouse', 'quantity', 'location')
    list_filter = ('warehouse', 'product__category')
    search_fields = ('product__name', 'product__sku')
    ordering = ('warehouse', 'product')
    
    autocomplete_fields = ('product', 'warehouse')
    readonly_fields = ('quantity', 'created_at', 'updated_at')

    fieldsets = (
        ('بيانات التخزين', {
            'fields': ('product', 'warehouse', 'location')
        }),
        ('الأرصدة', {
            'fields': ('quantity',)
        }),
    )


# ==========================================
# 4. أذونات المخازن وحركاتها (Master-Detail)
# ==========================================

class StockMovementInline(TabularInline):
    """سطور الإذن (حركات الأصناف)"""
    model = StockMovement
    extra = 1  # سطر واحد فارغ افتراضياً
    autocomplete_fields = ('product',)
    
    def has_change_permission(self, request, obj=None):
        """منع تعديل السطور بعد حفظ الإذن"""
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        """منع حذف السطور بعد حفظ الإذن"""
        if obj is not None:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(StockDocument)
class StockDocumentAdmin(ModelAdmin):
    """إذن المخزن الرئيسي (الأب)"""
    list_display = ('id', 'document_type', 'warehouse', 'date', 'reference', 'created_by')
    list_filter = ('document_type', 'warehouse', 'date')
    search_fields = ('reference', 'notes', 'warehouse__name')
    ordering = ('-created_at',)
    
    autocomplete_fields = ('warehouse', 'journal_entry')
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')

    # دمج السطور (الابن) داخل صفحة الإذن (الأب)
    inlines = [StockMovementInline]

    fieldsets = (
        ('بيانات الإذن المخزني', {
            'fields': ('document_type', 'warehouse', 'date')
        }),
        ('التوثيق والارتباطات', {
            'fields': ('reference', 'journal_entry', 'notes')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'created_by', 'updated_at', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        """تسجيل الموظف اللي عمل الإذن أوتوماتيك"""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        """منع تعديل الإذن بالكامل بعد حفظه للحفاظ على دقة الأرصدة"""
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)