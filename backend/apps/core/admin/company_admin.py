from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import Company
from .inlines import BranchInline, AttachmentInline

@admin.register(Company)
class CompanyAdmin(ModelAdmin):
    list_display = ('name', 'email', 'phone', 'created_at')
    search_fields = ('name', 'email', 'tax_number')
    inlines = [BranchInline, AttachmentInline]
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': ('name', 'logo', 'email', 'phone', 'website', 'address')
        }),
        ('البيانات القانونية', {
            'fields': ('tax_number', 'commercial_record'),
            'classes': ('collapse',),
        }),
        ('سجلات النظام', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',),
        }),
    )