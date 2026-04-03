from django.contrib import admin
from unfold.admin import ModelAdmin
from ..models import Sequence


@admin.register(Sequence)
class SequenceAdmin(ModelAdmin):
    list_display = ('key', 'current_value', 'prefix', 'formatted_next')
    search_fields = ('key', 'prefix')
    readonly_fields = ('formatted_next',)

    @admin.display(description="الرقم التالي المتوقع")
    def formatted_next(self, obj):
        return f"{obj.prefix}{str(obj.current_value + 1).zfill(obj.padding)}"