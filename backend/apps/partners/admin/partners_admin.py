from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import Partner
from decimal import Decimal

@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    # 1. القائمة الرئيسية (أهم البيانات اللي بتظهر في الجدول الخارجي)
    list_display = (
        'code', 
        'name', 
        'partner_type', 
        'phone', 
        'get_current_balance', # مهم جداً يظهر بره للمتابعة السريعة
        'is_active'
    )
    
    # 2. الفلاتر الجانبية (عشان تفصل العملاء عن الموردين أو تفلتر بالمدينة)
    list_filter = (
        'partner_type', 
        'is_active', 
        'city',
        'created_at'
    )
    
    # 3. حقول البحث (بحث شامل وسريع)
    search_fields = (
        'code', 
        'name', 
        'phone', 
        'mobile',
        'tax_number', 
        'commercial_record'
    )
    
    # الترتيب الافتراضي
    ordering = ('-created_at',)
    
    # 4. الحقول المحمية (الكود والرصيد الحالي وحقول النظام)
    readonly_fields = (
        'get_current_balance',
        'code', 
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by'
    )

    # 5. تقسيم صفحة الإضافة والتعديل بشكل مريح جداً للعين (Fieldsets)
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
                # التعديل هنا: دمجنا الرصيد الثابت مع الرصيد الفعلي (المحسوب) في سطر واحد
                ('get_current_balance'), 
                'responsible',
                'notes'
            ),
            'description': 'الرصيد الافتتاحي يتم ضبطه مرة واحدة فقط. الرصيد الفعلي يتحدث تلقائياً مع حركات الفواتير والقيود.'
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
        # تأمين القيمة في حال كانت None
        balance = obj.current_balance or Decimal('0.00')
        
        if balance > 0:
            return f"{balance} (له)" if obj.partner_type != 'customer' else f"{balance} (عليه)"
        elif balance < 0:
            return f"{abs(balance)} (عليه)" if obj.partner_type != 'customer' else f"{abs(balance)} (له)"
        return "0.00"
    
    get_current_balance.short_description = "الرصيد الفعلي (من الحسابات)"