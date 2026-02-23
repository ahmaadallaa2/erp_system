from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import Partner

@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    # 1. القائمة الرئيسية (أهم البيانات اللي محتاج تشوفها من بره)
    list_display = (
        'code', 
        'name', 
        'partner_type', 
        'entity_type', 
        'phone', 
        'is_active'
    )
    
    # 2. الفلاتر (عشان تفصل العملاء عن الموردين بضغطة زرار)
    list_filter = (
        'partner_type', 
        'entity_type', 
        'is_active', 
        'created_at'
    )
    
    # 3. حقول البحث (بحث شامل بالكود، الاسم، التليفون، أو حتى السجل التجاري)
    search_fields = (
        'code', 
        'name', 
        'phone', 
        'tax_number', 
        'commercial_record'
    )
    
    # الترتيب الافتراضي (الأحدث أولاً أو أبجدياً بالاسم)
    ordering = ('-created_at',)
    
    # 4. الحقول المحمية (الكود بيتولد أوتوماتيك وحقول النظام)
    readonly_fields = (
        'code', 
        'created_at', 
        'updated_at', 
        'created_by', 
        'updated_by'
    )

    # 5. تقسيم صفحة الإضافة بشكل مريح للعين (Fieldsets)
    fieldsets = (
        ('البيانات الأساسية والتصنيف', {
            'fields': (
                ('name', 'code'),
                ('partner_type', 'entity_type'),
                'is_active'
            )
        }),
        ('بيانات التواصل والعنوان', {
            'fields': (
                ('phone', 'email'),
                'address'
            )
        }),
        ('البيانات القانونية والضريبية', {
            'fields': (
                'tax_number', 
                'commercial_record'
            ),
            'description': 'هذه البيانات إلزامية في حالة كان الكيان "شركة" لطباعتها على الفواتير الضريبية.'
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'), 
                ('created_by', 'updated_by')
            ),
            'classes': ('collapse',),
        }),
    )