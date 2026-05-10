from django.contrib.contenttypes.admin import GenericTabularInline
from unfold.admin import TabularInline
from apps.core.models import Attachment, Branch


class AttachmentInline(GenericTabularInline):
    """
    خانة رفع الملفات داخل أي صفحة أدمن أخرى.
    """
    model = Attachment
    extra = 1
    fields = ('file', 'name', 'note')
    ct_field = "content_type"
    ct_fk_field = "object_id"


class BranchInline(TabularInline):
    """
    إضافة الفروع مباشرة من صفحة تعديل الشركة.
    """
    model = Branch
    extra = 0
    fields = ('name', 'code', 'phone', 'is_active')
    readonly_fields = ('code',)
    show_change_link = True
