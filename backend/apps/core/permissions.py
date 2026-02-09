from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

# --- 1. تعريف أسماء المجموعات (Roles) ---
# بنحطها في متغيرات عشان نستخدمها في السيستم كله من غير ما نغلط في الإملاء
GROUP_SUPER_ADMIN = 'Super Admin'  # له كل الصلاحيات
GROUP_MANAGER = 'Manager'          # مدير (فرع أو قسم)
GROUP_ACCOUNTANT = 'Accountant'    # محاسب
GROUP_INVENTORY = 'Inventory Staff'# أمين مخزن
GROUP_SALES = 'Sales Agent'        # موظف مبيعات

SYSTEM_GROUPS = [
    GROUP_SUPER_ADMIN,
    GROUP_MANAGER,
    GROUP_ACCOUNTANT,
    GROUP_INVENTORY,
    GROUP_SALES
]

# --- 2. دوال مساعدة للتحقق من الصلاحيات ---

def is_in_group(user, group_name):
    """
    تتأكد هل المستخدم ينتمي لمجموعة معينة أم لا.
    Usage: is_in_group(user, GROUP_MANAGER)
    """
    if not user or not user.is_authenticated:
        return False
    # لو هو سوبر يوزر، اعتبره موجود في أي جروب
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()

def has_object_permission(user, obj, permission_type='view'):
    """
    تتأكد هل المستخدم يملك الصلاحية على مستوى السجل (Object Level)
    القاعدة: صاحب السجل (Created_by) دايماً له حق التعديل، إلا لو السجل اتقفل.
    """
    # السوبر يوزر له حق التصرف دائماً
    if user.is_superuser:
        return True

    # صاحب السجل
    if hasattr(obj, 'created_by') and obj.created_by == user:
        return True
    
    # هنا ممكن نضيف منطق: هل هو مديره المباشر؟ هل في نفس الفرع؟
    return False

# --- 3. دالة تهيئة النظام (Setup) ---
# الدالة دي بنشغلها مرة واحدة عشان تزرع الجروبات دي في الداتابيز
def create_default_groups():
    created_count = 0
    for group_name in SYSTEM_GROUPS:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            created_count += 1
            print(f"Created Group: {group_name}")
    return created_count