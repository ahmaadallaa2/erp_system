from django.contrib import admin
from unfold.admin import ModelAdmin
from apps.accounting.models.journal import Journal # تأكد من المسار

@admin.register(Journal)
class JournalAdmin(ModelAdmin):
    list_display = ('code', 'name', 'type', 'default_account')
    list_filter = ('type',)
    search_fields = ('code', 'name')
    ordering = ('code',)
    autocomplete_fields = ('default_account',)

    fieldsets = (
        ('بيانات الدفتر', {
            'fields': (('code', 'name'), 'type', 'default_account')
        }),
    )