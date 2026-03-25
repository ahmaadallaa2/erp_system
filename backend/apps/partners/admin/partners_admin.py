from django.contrib import admin
from django.db.models import Sum, DecimalField, F, Case, When, Q
from django.db.models.functions import Coalesce
from unfold.admin import ModelAdmin
from decimal import Decimal
from ..models import Partner

@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    # =========================================================================
    # 🚀 تحسين الأداء والصلاحيات (Query Optimization & RBAC)
    # =========================================================================
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # 1. فلترة الصلاحيات بذكاء (Fetching Groups ONCE in memory)
        # بدل ما نعمل query لكل جروب، بنجيب أسامي الجروبات كلها مرة واحدة ونخزنها في set
        user_groups = set(request.user.groups.values_list('name', flat=True))
        
        if not request.user.is_superuser:
            if 'فريق المبيعات' in user_groups:
                qs = qs.filter(partner_type='customer')
            elif 'أمناء المخازن' in user_groups or 'الإدارة المالية' in user_groups:
                qs = qs.filter(partner_type='supplier')

        # 2. حساب الرصيد الفعلي عبر الـ Annotate لحل مشكلة N+1 Query
        qs = qs.annotate(
            total_debit=Coalesce(
                Sum('journal_items__debit', filter=Q(journal_items__entry__status='posted')), 
                Decimal('0.00'), 
                output_field=DecimalField()
            ),
            total_credit=Coalesce(
                Sum('journal_items__credit', filter=Q(journal_items__entry__status='posted')), 
                Decimal('0.00'), 
                output_field=DecimalField()
            ),
            # حساب الرصيد الصافي في الـ DB بناءً على نوع الشريك
            annotated_balance=Case(
                When(partner_type='customer', then=F('initial_balance') + F('total_debit') - F('total_credit')),
                default=F('initial_balance') + F('total_credit') - F('total_debit'),
                output_field=DecimalField()
            )
        )
        return qs

    # =========================================================================
    # 1. القائمة الرئيسية (List View)
    # =========================================================================
    list_display = (
        'code', 
        'name', 
        'partner_type', 
        'phone', 
        'get_current_balance', 
        'is_active'
    )
    
    list_filter = (
        'partner_type', 
        'is_active', 
        'city',
        'created_at'
    )
    
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

    # =========================================================================
    # 2. تقسيم صفحة الإضافة والتعديل (Fieldsets)
    # =========================================================================
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
            'description': 'الرصيد الافتتاحي يتم ضبطه مرة واحدة فقط. الرصيد الفعلي يتحدث تلقائياً من الحسابات.'
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'), 
                ('created_by', 'updated_by')
            ),
            'classes': ('collapse',),
        }),
    )

    # =========================================================================
    # 3. الدوال المحسوبة والمساعدة
    # =========================================================================
    @admin.display(description="الرصيد الفعلي (من الحسابات)", ordering='annotated_balance')
    def get_current_balance(self, obj):
        """يعرض الرصيد المحسوب مسبقاً من الـ QuerySet"""
        
        # حماية لو كان Object جديد في صفحة الـ Add
        if not obj or not obj.pk:
            return "0.00"

        # نقرأ القيمة المحسوبة عبر الـ Annotate (أو نرجع للـ property لو مش موجودة كاحتياط)
        balance = getattr(obj, 'annotated_balance', obj.current_balance) or Decimal('0.00')
        
        if balance > 0:
            return f"{balance:,.2f} (له)" if obj.partner_type != 'customer' else f"{balance:,.2f} (عليه)"
        elif balance < 0:
            return f"{abs(balance):,.2f} (عليه)" if obj.partner_type != 'customer' else f"{abs(balance):,.2f} (له)"
        
        return "0.00"

    def save_model(self, request, obj, form, change):
        """حفظ سجلات الـ Audit أوتوماتيكياً"""
        if not change: # لو سجل جديد
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)