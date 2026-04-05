from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

# استدعاء أسماء المجموعات من ملف الصلاحيات اللي لسه عاملينه
from backend.apps.users.roles import (
    GROUP_SUPER_ADMIN, 
    GROUP_MANAGER, 
    GROUP_ACCOUNTANT, 
    GROUP_INVENTORY, 
    GROUP_SALES,
    create_default_groups
)

class Command(BaseCommand):
    help = 'إنشاء مجموعات النظام الأساسية وربطها بالصلاحيات المناسبة'

    def handle(self, *args, **kwargs):
        # 1. إنشاء المجموعات كأسماء أولاً (باستخدام الدالة اللي عملناها)
        self.stdout.write("جاري تهيئة المجموعات...")
        create_default_groups()

        # 2. قاموس (Dictionary) يربط كل مجموعة بصلاحياتها (Codenames)
        # ملاحظة: جانجو بيسمي الصلاحيات كده (add_modelname, view_modelname, change_modelname)
        ROLE_PERMISSIONS = {
            GROUP_SALES: [
                'view_customer', 'add_customer', 'change_customer',
                'view_product', # يشوف المنتجات عشان يبيعها بس ميعرفش يضيف منتج
                'view_warehouse', # يشوف المخزن
                'view_salesinvoice', 'add_salesinvoice', 'change_salesinvoice',
            ],
            
            GROUP_INVENTORY: [
                'view_product', 'add_product', 'change_product',
                'view_warehouse', 'add_warehouse', 'change_warehouse',
                'view_inventorymovement', 'add_inventorymovement',
            ],
            
            GROUP_ACCOUNTANT: [
                'view_account', 'add_account', 'change_account',
                'view_journalentry', 'add_journalentry', 'change_journalentry',
                'view_purchaseinvoice', 'add_purchaseinvoice', 'change_purchaseinvoice',
                'view_salesinvoice', # يشوف المبيعات عشان يراجعها لكن ميعدلش فيها
                'view_supplier', 'add_supplier', 'change_supplier',
            ],
            
            GROUP_MANAGER: [
                # المدير غالباً بياخد صلاحيات عرض (View) لكل حاجة في السيستم عشان التقارير
                'view_customer', 'view_product', 'view_warehouse', 
                'view_salesinvoice', 'view_purchaseinvoice', 
                'view_journalentry', 'view_account', 'view_inventorymovement'
            ]
            # مدير النظام (Super Admin) مش بنحطله صلاحيات هنا لأنه by default بياخد كل حاجة
        }

        # 3. حلقة تكرارية لربط الصلاحيات بالمجموعات
        for group_name, codenames in ROLE_PERMISSIONS.items():
            try:
                group = Group.objects.get(name=group_name)
                # بنجيب كل الصلاحيات اللي أسماءها موجودة في اللستة بتاعة المجموعة دي
                permissions = Permission.objects.filter(codename__in=codenames)
                
                # بنحط الصلاحيات دي جوه المجموعة
                group.permissions.set(permissions)
                self.stdout.write(self.style.SUCCESS(f'تم ربط الصلاحيات بنجاح للمجموعة: {group_name}'))
            
            except Group.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'المجموعة {group_name} غير موجودة!'))

        self.stdout.write(self.style.SUCCESS('--- تم الانتهاء من إعداد نظام الصلاحيات بالكامل ---'))