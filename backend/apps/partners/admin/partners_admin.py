from decimal import Decimal

from django.contrib import admin
from django.db.models import Sum, DecimalField, F, Case, When, Q
from django.db.models.functions import Coalesce
from unfold.admin import ModelAdmin

from ..models import Partner


@admin.register(Partner)
class PartnerAdmin(ModelAdmin):
    # =========================================================================
    # 1. تحسين الأداء + فلترة الصلاحيات + Multi-company
    # =========================================================================
    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related('company', 'responsible')

        user_groups = set(request.user.groups.values_list('name', flat=True))

        # فلترة حسب الشركة للمستخدمين العاديين
        if not request.user.is_superuser and getattr(request.user, 'company_id', None):
            qs = qs.filter(company_id=request.user.company_id)

        # فلترة حسب الدور الوظيفي
        if not request.user.is_superuser:
            if 'فريق المبيعات' in user_groups:
                qs = qs.filter(
                    partner_type__in=[
                        Partner.PartnerType.CUSTOMER,
                        Partner.PartnerType.BOTH,
                    ]
                )
            elif 'أمناء المخازن' in user_groups or 'الإدارة المالية' in user_groups:
                qs = qs.filter(
                    partner_type__in=[
                        Partner.PartnerType.SUPPLIER,
                        Partner.PartnerType.BOTH,
                    ]
                )

        # حساب الرصيد من قاعدة البيانات لتجنب N+1 Query
        qs = qs.annotate(
            total_debit=Coalesce(
                Sum(
                    'journal_items__debit',
                    filter=Q(journal_items__entry__status='posted')
                ),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            total_credit=Coalesce(
                Sum(
                    'journal_items__credit',
                    filter=Q(journal_items__entry__status='posted')
                ),
                Decimal('0.00'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            ),
            annotated_balance=Case(
                When(
                    partner_type=Partner.PartnerType.CUSTOMER,
                    then=F('initial_balance') + F('total_debit') - F('total_credit')
                ),
                default=F('initial_balance') + F('total_credit') - F('total_debit'),
                output_field=DecimalField(max_digits=14, decimal_places=2)
            )
        )

        return qs

    # =========================================================================
    # 2. القائمة الرئيسية
    # =========================================================================
    list_display = (
        'code',
        'name',
        'company',
        'partner_type',
        'phone',
        'get_current_balance',
        'is_active',
    )

    list_filter = (
        'company',
        'partner_type',
        'is_active',
        'city',
        'created_at',
    )

    search_fields = (
        'code',
        'name',
        'phone',
        'mobile',
        'email',
        'tax_number',
        'commercial_record',
        'company__name',
    )

    ordering = ('-created_at',)

    readonly_fields = (
        'get_current_balance',
        'code',
        'created_at',
        'updated_at',
        'created_by',
        'updated_by',
    )

    # =========================================================================
    # 3. تقسيم صفحة الإضافة والتعديل
    # =========================================================================
    fieldsets = (
        ('البيانات الأساسية والتصنيف', {
            'fields': (
                'company',
                ('name', 'code'),
                ('partner_type', 'is_active'),
            )
        }),
        ('بيانات التواصل والعنوان', {
            'fields': (
                ('phone', 'mobile'),
                ('email', 'website'),
                ('city', 'address'),
            )
        }),
        ('البيانات القانونية والضريبية', {
            'fields': (
                ('tax_number', 'commercial_record'),
            ),
            'description': 'البيانات الضريبية ضرورية للشركات لطباعتها على الفواتير الرسمية.',
        }),
        ('البيانات المالية والإدارية', {
            'fields': (
                ('credit_limit', 'initial_balance'),
                ('get_current_balance',),
                'responsible',
                'notes',
            ),
            'description': 'الرصيد الافتتاحي يتم ضبطه مرة واحدة فقط. الرصيد الفعلي يتحدث تلقائياً من الحسابات.',
        }),
        ('سجلات النظام', {
            'fields': (
                ('created_at', 'updated_at'),
                ('created_by', 'updated_by'),
            ),
            'classes': ('collapse',),
        }),
    )

    # =========================================================================
    # 4. تخصيص الحقول حسب المستخدم
    # =========================================================================
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # تقييد الشركات للمستخدم غير الـ superuser
        if not request.user.is_superuser and 'company' in form.base_fields:
            if getattr(request.user, 'company_id', None):
                form.base_fields['company'].queryset = form.base_fields['company'].queryset.filter(
                    pk=request.user.company_id
                )
                form.base_fields['company'].initial = request.user.company_id

        # تقييد الموظف المسؤول لنفس الشركة
        if 'responsible' in form.base_fields and not request.user.is_superuser:
            if getattr(request.user, 'company_id', None):
                form.base_fields['responsible'].queryset = form.base_fields['responsible'].queryset.filter(
                    company_id=request.user.company_id,
                    is_active=True
                )

        return form

    # =========================================================================
    # 5. الدوال المحسوبة والمساعدة
    # =========================================================================
    @admin.display(description="الرصيد الفعلي (من الحسابات)", ordering='annotated_balance')
    def get_current_balance(self, obj):
        if not obj or not obj.pk:
            return "0.00"

        balance = getattr(obj, 'annotated_balance', None)
        if balance is None:
            balance = obj.current_balance or Decimal('0.00')

        if balance > 0:
            if obj.partner_type == Partner.PartnerType.CUSTOMER:
                return f"{balance:,.2f} (عليه)"
            return f"{balance:,.2f} (له)"

        if balance < 0:
            if obj.partner_type == Partner.PartnerType.CUSTOMER:
                return f"{abs(balance):,.2f} (له)"
            return f"{abs(balance):,.2f} (عليه)"

        return "0.00"

    # =========================================================================
    # 6. الحفظ
    # =========================================================================
    def save_model(self, request, obj, form, change):
        # لو المستخدم غير superuser ومربوط بشركة، نثبت الشركة تلقائياً
        if not request.user.is_superuser and getattr(request.user, 'company_id', None):
            obj.company_id = request.user.company_id

        if not change and not obj.created_by_id:
            obj.created_by = request.user
        obj.updated_by = request.user

        super().save_model(request, obj, form, change)