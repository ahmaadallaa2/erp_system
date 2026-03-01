from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.accounting.models.account import Account # تأكد من المسار

@admin.register(Account)
class AccountAdmin(ModelAdmin):
    list_display = (
        'code', 'name', 'account_type', 'parent', 
        'allow_reconciliation', 'is_active', 'get_current_balance'
    )
    list_filter = ('account_type', 'is_active', 'allow_reconciliation')
    search_fields = ('code', 'name')
    readonly_fields = ('get_current_balance', 'created_at', 'updated_at')
    ordering = ('code',)
    autocomplete_fields = ('parent',) # عشان لو الشجرة كبرت تعرف تبحث عن الحساب الأب بسهولة

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (('code', 'name'), 'account_type', 'parent')
        }),
        ('إعدادات متقدمة', {
            'fields': ('allow_reconciliation', 'is_active', 'get_current_balance')
        }),
    )

    def get_current_balance(self, obj):
        return obj.current_balance
    get_current_balance.short_description = "الرصيد الفعلي"