from django.core.management.base import BaseCommand
from apps.core.permissions import create_default_groups

class Command(BaseCommand):
    help = 'إنشاء مجموعات المستخدمين الافتراضية للنظام (Roles)'

    def handle(self, *args, **options):
        self.stdout.write('بدء تهيئة المجموعات...')
        count = create_default_groups()
        if count > 0:
            self.stdout.write(self.style.SUCCESS(f'تم إنشاء {count} مجموعة بنجاح!'))
        else:
            self.stdout.write(self.style.WARNING('المجموعات موجودة بالفعل.'))