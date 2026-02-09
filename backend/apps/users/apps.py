from django.apps import AppConfig

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'  # <--- تأكد إنها مكتوبة كده
    verbose_name = "إدارة المستخدمين"