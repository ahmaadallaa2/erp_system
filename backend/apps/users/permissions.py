from django.contrib.auth.models import Group

# --- 1. تعريف أسماء المجموعات (Roles) باللغة العربية ---
# بنحطها في متغيرات عشان نستخدمها في السيستم كله من غير ما نغلط في الإملاء
GROUP_SUPER_ADMIN = 'مدير النظام'           # له كل الصلاحيات
GROUP_MANAGER = 'مدير فرع'                 # مدير (فرع أو قسم)
GROUP_ACCOUNTANT = 'الإدارة المالية'        # محاسبات وقيود
GROUP_INVENTORY = 'أمناء المخازن'           # جرد وحركات مخزنية
GROUP_SALES = 'فريق المبيعات'              # فواتير وعملاء

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
            print(f"تم إنشاء مجموعة بنجاح: {group_name}")
        else:
            print(f"المجموعة موجودة مسبقاً: {group_name}")
    return created_count