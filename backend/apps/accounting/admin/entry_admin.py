from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from apps.accounting.models.entry import JournalEntry, JournalItem # تأكد من المسار

class JournalItemInline(TabularInline):
    model = JournalItem
    extra = 2 # المحاسب دايماً بيحتاج سطرين على الأقل (مدين ودائن)
    fields = ('account', 'partner', 'description', 'debit', 'credit')
    autocomplete_fields = ('account', 'partner')

@admin.register(JournalEntry)
class JournalEntryAdmin(ModelAdmin):
    list_display = ('entry_number', 'journal', 'date', 'reference', 'status')
    list_filter = ('status', 'journal', 'date')
    search_fields = ('entry_number', 'reference', 'notes')
    inlines = [JournalItemInline]
    readonly_fields = ('entry_number', 'created_at', 'updated_at')
    ordering = ('-date', '-id')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                ('entry_number', 'date'), 
                ('journal', 'status')
            )
        }),
        ('الارتباطات والملاحظات', {
            'fields': ('reference', 'notes')
        }),
    )