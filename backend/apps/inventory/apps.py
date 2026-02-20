from django.apps import AppConfig

class InventoryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.inventory'  # <--- مهم جداً تكتب المسار كامل
    verbose_name = "المخازن والمنتجات"

    def ready(self):
        #استيراد الإشارات هنا عشان تتفعل
        import apps.inventory.signals