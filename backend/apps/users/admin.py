from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _

from unfold.admin import ModelAdmin
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm as BaseUserChangeForm,
    UserCreationForm as BaseUserCreationForm
)

from .models import User


class CustomUserChangeForm(BaseUserChangeForm):
    class Meta:
        model = User
        fields = '__all__'


class CustomUserCreationForm(BaseUserCreationForm):
    class Meta:
        model = User
        fields = ('email', 'full_name', 'user_type', 'company', 'branch')


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin, ModelAdmin):
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = ('email', 'full_name', 'user_type', 'company', 'branch', 'is_active')
    list_filter = ('user_type', 'company', 'branch', 'is_staff', 'is_active')
    search_fields = ('email', 'full_name', 'phone', 'job_title')
    ordering = ('-date_joined',)
    readonly_fields = ('last_login', 'date_joined')
    filter_horizontal = ('groups', 'user_permissions')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('البيانات الشخصية'), {
            'fields': ('full_name', 'phone', 'job_title')
        }),
        (_('هيكل العمل والصلاحيات'), {
            'fields': ('user_type', 'company', 'branch')
        }),
        (_('صلاحيات دجانغو'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('التواريخ الهامة'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',),
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'user_type', 'company', 'branch', 'password1', 'password2'),
        }),
    )