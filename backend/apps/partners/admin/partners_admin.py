from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import Partner
from decimal import Decimal

@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    # --- تعديل: فلترة البيانات بناءً على الصلاحيات (الذكاء الاصطناعي للسيستم) ---
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # لو سوبر يوزر، اعرض كل حاجة
        if request.user.is_superuser:
            return qs
        
        # لو الموظف في مجموعة المبيعات، اعرض العملاء فقط
        if request.user.groups.filter(name='فريق المبيعات').exists():
            return qs.filter(partner_type='customer')
            
        # لو الموظف في مجموعة المشتريات أو المخازن، اعرض الموردين فقط
        if request.user.groups.filter(name='أمناء المخازن').exists() or \
           request.user.groups.filter(name='الإدارة المالية').exists():
            return qs.filter(partner_type='supplier')
            
        return qs

    # 1. القائمة الرئيسية
    list_display = (
        'code', 
        'name', 
        'partner_type', 
        'phone', 
        'get_current_balance', 
        'is_active'
    )
    
    # 2. الفلاتر الجانبية
    list_filter = (
        'partner_type', 
        'is_active', 
        'city',
        'created_at'
    )
    
    # 3. حقول البحث
    search_fields = (
        'code', 
        'name', 
        'phone', 
        'mobile',
        'tax_number', 
        'commercial_record'
    )
    
    ordering = ('-created_at',)
    
    readonly_fields = (
        'get_current_balance',
        'code', 
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by'
    )

    # 5. تقسيم صفحة الإضافة والتعديل (Fieldsets)
    fieldsets = (
        ('البيانات الأساسية والتصنيف', {
            'fields': (
                ('name', 'code'),
                ('partner_type', 'is_active')
            )
        }),
        ('بيانات التواصل والعنوان', {
            'fields': (
                ('phone', 'mobile'),
                ('email', 'website'),
                ('city', 'address')
            )
        }),
        ('البيانات القانونية والضريبية', {
            'fields': (
                ('tax_number', 'commercial_record'),
            ),
            'description': 'البيانات الضريبية ضرورية للشركات لطباعتها على الفواتير الرسمية.'
        }),
        ('البيانات المالية والإدارية', {
            'fields': (
                ('credit_limit', 'initial_balance'),
                ('get_current_balance',), # الرصيد الفعلي
                'responsible',
                'notes'
            ),
            'description': 'الرصيد الافتتاحي يتم ضبطه مرة واحدة فقط. الرصيد الفعلي يتحدث تلقائياً.'
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'), 
                ('created_by', 'updated_by')
            ),
            'classes': ('collapse',),
        }),
    )

    def get_current_balance(self, obj):
        balance = obj.current_balance or Decimal('0.00')
        if balance > 0:
            return f"{balance} (له)" if obj.partner_type != 'customer' else f"{balance} (عليه)"
        elif balance < 0:
            return f"{abs(balance)} (عليه)" if obj.partner_type != 'customer' else f"{abs(balance)} (له)"
        return "0.00"
    
    get_current_balance.short_description = "الرصيد الفعلي (من الحسابات)"

    # --- لمسة احترافية إضافية للعرض: تعبئة حقل created_by أوتوماتيكياً ---
    def save_model(self, request, obj, form, change):
        if not change: # لو سجل جديد
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)