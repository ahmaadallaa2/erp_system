from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.accounting.models.payment import Payment
from apps.accounting.services.accounting_service import AccountingService
from django.contrib import messages

@admin.register(Payment)
class PaymentAdmin(ModelAdmin):
    list_display = ('name', 'partner', 'payment_type', 'payment_method', 'amount', 'date', 'has_journal_entry')
    list_filter = ('payment_type', 'payment_method', 'date')
    search_fields = ('name', 'partner__name', 'reference')
    autocomplete_fields = ('partner',)
    
    # الحقول دي السيستم بيكريتها لوحده فبنقفلها
    readonly_fields = ('name', 'journal_entry', 'created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('بيانات السند الأساسية', {
            'fields': (
                ('payment_type', 'payment_method'),
                ('partner', 'amount'),
                'date'
            )
        }),
        ('معلومات إضافية', {
            'fields': (
                'reference', 
                'notes',
                'journal_entry' # هيظهر هنا القيد بعد ما يتكريت
            )
        }),
    )

    def has_journal_entry(self, obj):
        return bool(obj.journal_entry)
    has_journal_entry.short_description = "مُرحل حسابياً؟"
    has_journal_entry.boolean = True

    # التريكة السحرية: لما المحاسب يدوس حفظ، ننده على السيرفيس تكريت القيد!
    def save_model(self, request, obj, form, change):
        # 1. نحفظ السند الأول
        super().save_model(request, obj, form, change)
        
        # 2. شلنا شرط is_new.. لو السند ملوش قيد، حاول ترحله فوراً
        if not obj.journal_entry:
            try:
                success, msg = AccountingService.create_payment_entry(obj)
                
                if success:
                    messages.success(request, f"تم الترحيل المحاسبي بنجاح: {msg}")
                else:
                    messages.error(request, f"⚠️ السند محفوظ بس مترحلش حسابياً: {msg}")
                    
            except Exception as e:
                messages.error(request, f"❌ خطأ برمجي في الحسابات: {str(e)}")