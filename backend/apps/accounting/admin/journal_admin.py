# apps/accounting/admin/journal_admin.py
from django.contrib import admin
from django.db.models import Count
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from apps.accounting.models.journal import Journal


@admin.register(Journal)
class JournalAdmin(ModelAdmin):

    # =========================================================================
    # 1. إعدادات القايمة (List View)
    # =========================================================================
    list_display  = ('code', 'name', 'get_type_badge', 'default_account', 'get_entries_count')
    list_filter   = ('type',)
    search_fields = ('code', 'name')
    ordering      = ('code',)

    autocomplete_fields = ('default_account',)
    readonly_fields     = ('get_entries_count', 'created_at', 'updated_at')

    # =========================================================================
    # 2. تنظيم الحقول (Fieldsets)
    # =========================================================================
    fieldsets = (
        (_('بيانات الدفتر'), {
            'fields': (
                ('code', 'name'),
                'type',
                'default_account',
            )
        }),
        (_('معلومات إضافية'), {
            'classes': ('collapse',),
            'fields': (
                'get_entries_count',
                'created_at',
                'updated_at',
            )
        }),
    )

    # =========================================================================
    # 3. تحسين الأداء (Query Optimization)
    # =========================================================================
    def get_queryset(self, request):
        """
        تحسين الاستعلام لجمع عدد القيود وجلب بيانات الحساب الافتراضي في Query واحد،
        مما يمنع مشكلة N+1 ويجعل تحميل الصفحة سريعاً جداً.
        """
        qs = super().get_queryset(request)
        return qs.select_related('default_account').annotate(
            entries_count=Count('entries')
        )

    # =========================================================================
    # 4. الأعمدة المحسوبة (Computed Columns)
    # =========================================================================
    @admin.display(description=_('النوع'))
    def get_type_badge(self, obj):
        """يعرض نوع الدفتر بلون مميز لكل نوع."""
        colors = {
            'sale':     ('#1b5e20', '#e8f5e9'),  # أخضر غامق
            'purchase': ('#b71c1c', '#ffebee'),  # أحمر غامق
            'cash':     ('#e65100', '#fff3e0'),  # برتقالي
            'bank':     ('#0d47a1', '#e3f2fd'),  # أزرق
            'general':  ('#4a148c', '#f3e5f5'),  # بنفسجي
        }
        text_color, bg_color = colors.get(obj.type, ('#333', '#eee'))
        return format_html(
            '<span style="'
            'background-color: {}; color: {}; '
            'padding: 2px 10px; border-radius: 12px; '
            'font-size: 12px; font-weight: bold;">'
            '{}</span>',
            bg_color, text_color,
            obj.get_type_display()
        )

    @admin.display(description=_('عدد القيود'), ordering='entries_count')
    def get_entries_count(self, obj):
        """
        يقرأ عدد القيود المسجلة المحسوب مسبقاً من get_queryset.
        تمت إضافة حماية لشاشة الـ Add View عندما يكون obj جديداً وليس له ID.
        """
        # حماية شاشة الإضافة (Add View): لو الدفتر لسه بيتكريت
        if not obj or not obj.pk:
            return format_html('<span style="color: #9e9e9e;">{}</span>', '—')

        # نقرأ القيمة من الـ annotation مباشرة
        count = getattr(obj, 'entries_count', 0)
        
        if count == 0:
            return format_html('<span style="color: #9e9e9e;">{}</span>', '—')
            
        return format_html(
            '<span style="font-weight: bold;">{}</span>',
            count
        )