from django.contrib import admin
from django.core.exceptions import ValidationError
from unfold.admin import ModelAdmin, TabularInline

from .models import (
    Category,
    Unit,
    Product,
    Warehouse,
    StockBalance,
    StockTransaction,
    StockMovement,
)


# ==========================================
# 1. الأساسيات والتصنيفات (Lookup Tables)
# ==========================================

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'parent', 'company', 'is_active', 'created_at')
    list_filter = ('company', 'parent', 'is_active')
    search_fields = ('name',)
    ordering = ('company', 'name')
    autocomplete_fields = ('company', 'parent')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('company', 'name', 'parent', 'is_active')
        }),
        ('تفاصيل إضافية', {
            'fields': ('description', 'icon')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Unit)
class UnitAdmin(ModelAdmin):
    list_display = ('name', 'short_name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'short_name')
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات الوحدة', {
            'fields': ('name', 'short_name', 'is_active')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ==========================================
# 2. المنتجات والمخازن (Master Data)
# ==========================================

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = (
        'name',
        'sku',
        'company',
        'category',
        'sale_price',
        'average_cost',
        'product_type',
        'is_active',
    )
    list_filter = ('company', 'category', 'product_type', 'is_active', 'created_at')
    search_fields = ('name', 'sku', 'barcode', 'description')
    ordering = ('company', 'name')

    autocomplete_fields = ('company', 'category', 'unit', 'income_account', 'expense_account')

    readonly_fields = (
        'sku',
        'average_cost',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

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
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Warehouse)
class WarehouseAdmin(ModelAdmin):
    list_display = ('code', 'name', 'company', 'warehouse_type', 'branch', 'keeper', 'is_active')
    list_filter = ('company', 'warehouse_type', 'branch', 'is_active')
    search_fields = ('code', 'name', 'branch__name', 'keeper__full_name', 'keeper__email')
    ordering = ('company', 'code', 'name')

    autocomplete_fields = ('company', 'branch', 'keeper')
    readonly_fields = ('code', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('company', 'name', 'code', 'warehouse_type', 'is_active')
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
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# ==========================================
# 3. الأرصدة (الرصيد اللحظي)
# ==========================================

@admin.register(StockBalance)
class StockBalanceAdmin(ModelAdmin):
    list_display = (
        'product',
        'warehouse',
        'quantity',
        'reserved_quantity',
        'available_quantity_display',
        'location',
    )
    list_filter = ('company', 'warehouse', 'product__category')
    search_fields = ('product__name', 'product__sku', 'warehouse__name')
    ordering = ('warehouse', 'product')

    autocomplete_fields = ('company', 'product', 'warehouse')

    readonly_fields = (
        'quantity',
        'reserved_quantity',
        'available_quantity_display',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    fieldsets = (
        ('بيانات التخزين', {
            'fields': ('company', 'product', 'warehouse', 'location', 'reorder_point')
        }),
        ('الأرصدة', {
            'fields': ('quantity', 'reserved_quantity', 'available_quantity_display')
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description="الكمية المتاحة")
    def available_quantity_display(self, obj):
        return obj.available_quantity


# ==========================================
# 4. الحركات المخزنية (Master-Detail)
# ==========================================

class StockMovementInline(TabularInline):
    """
    سطور الحركة المخزنية داخل المستند الرئيسي.
    """
    model = StockMovement
    extra = 1
    autocomplete_fields = ('product',)
    fields = ('product', 'quantity', 'unit_cost', 'note')

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)

    def has_add_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_add_permission(request, obj)


@admin.register(StockTransaction)
class StockTransactionAdmin(ModelAdmin):
    list_display = (
        'code',
        'transaction_type',
        'company',
        'source_warehouse',
        'destination_warehouse',
        'date',
        'status',
        'created_by',
    )
    list_filter = (
        'company',
        'transaction_type',
        'status',
        'source_warehouse',
        'date',
    )
    search_fields = (
        'code',
        'reference',
        'notes',
        'source_warehouse__name',
        'destination_warehouse__name',
    )
    ordering = ('-date', '-created_at')

    autocomplete_fields = ('company', 'source_warehouse', 'destination_warehouse', 'journal_entry')

    readonly_fields = (
        'code',
        'status',
        'posted_by',
        'posted_at',
        'created_at',
        'created_by',
        'updated_at',
        'updated_by',
    )

    inlines = [StockMovementInline]

    actions = ['post_transactions']

    fieldsets = (
        ('بيانات الحركة المخزنية', {
            'fields': (
                'company',
                'code',
                'transaction_type',
                'source_warehouse',
                'destination_warehouse',
                'date',
                'status',
            )
        }),
        ('التوثيق والارتباطات', {
            'fields': ('reference', 'journal_entry', 'notes')
        }),
        ('سجلات النظام', {
            'fields': (
                ('posted_by', 'posted_at'),
                'created_at',
                'created_by',
                'updated_at',
                'updated_by',
            ),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description="ترحيل الحركات المختارة")
    def post_transactions(self, request, queryset):
        from apps.inventory.services.stock_service import StockService

        posted_count = 0
        for obj in queryset:
            if obj.status == 'draft':
                try:
                    StockService.post_transaction(obj, user=request.user)
                    posted_count += 1
                except Exception as exc:
                    self.message_user(
                        request,
                        f"فشل ترحيل الحركة {obj.code or obj.pk}: {exc}",
                        level='error'
                    )

        if posted_count:
            self.message_user(request, f"تم ترحيل {posted_count} حركة بنجاح.")

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    def has_change_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.status in ('posted', 'cancelled'):
            return False
        return super().has_delete_permission(request, obj)

    def get_actions(self, request):
        actions = super().get_actions(request)
        actions.pop('delete_selected', None)
        return actions
