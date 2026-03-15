import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
load_dotenv()  # Load environment variables from .env file

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')  # Use environment variable or default for development

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'True'


ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
    'https://*.ngrok-free.dev',  # <-- السطر ده هو اللي هيحل المشكلة
]
# جانجو هيحدف أي حد مش مسجل على اللينك اللي اسمه 'login' (اللي هو الرئيسي دلوقتي)
LOGIN_URL = 'login' 

# بعد ما يكتب الإيميل والباسورد صح، هيروح فين؟ (هنوديه للداشبورد)
# غير مسار /dashboard/ للمسار بتاع الداشبورد بتاعتك
LOGIN_REDIRECT_URL = '/dashboard/' 

LOGOUT_REDIRECT_URL = 'login'

# Application definition

INSTALLED_APPS = [
    "unfold",  
    "unfold.contrib.filters",  # لو هتحتاج فلاتر متطورة
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    # my apps
    'apps.core',
    'apps.users',
    'apps.inventory',
    'apps.partners',
    'apps.purchases',
    'apps.accounting',
    'apps.sales'
]

MIDDLEWARE = [
    # 1. الأمان الأساسي (أول حاجة)
    'django.middleware.security.SecurityMiddleware',

    # 2. الجلسات (لازم قبل الـ Auth وقبل الـ CORS أحياناً)
    'django.contrib.sessions.middleware.SessionMiddleware',

    # 3. إعدادات الـ CORS (عشان الفرونت إند يكلم الباك إند)
    'corsheaders.middleware.CorsMiddleware',

    # 4. إعدادات عامة (زي الـ Slash في الـ URL)
    'django.middleware.common.CommonMiddleware',

    # 5. حماية الـ CSRF
    'django.middleware.csrf.CsrfViewMiddleware',

    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # 7. قفل السيستم (الميدلوير الجديد)
    'django.contrib.auth.middleware.LoginRequiredMiddleware', # <--- ضيف السطر ده هنا

    # 8. الرسائل المؤقتة
    'django.contrib.messages.middleware.MessageMiddleware',

    # 9. الميدلوير الخاص بينا (آخر واحد عشان يضمن إن الـ Auth خلص واليوزر بقى موجود)
    'apps.core.middleware.ThreadLocalMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # السطر السحري اللي بيشاور على فولدر templates اللي بره
        'DIRS': [BASE_DIR / 'templates'], 
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases
load_dotenv(os.path.join(BASE_DIR, '.env'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
 
CORS_ALLOWED_ORIGINS = [
"http://localhost:5173",

]
AUTH_USER_MODEL = 'users.User'
# إعدادات الذاكرة المؤقتة (Caching)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'erp_cache_table', # اسم تعريفي للكاش الخاص بك
    }
}

# إعدادات الـ APIs
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
}

# unfold admin settings


from django.urls import reverse_lazy

UNFOLD = {
    "SITE_TITLE": "ERP System | Enterprise",
    "SITE_HEADER": "نظام الإدارة المتكامل",
    "SITE_SYMBOL": "account_balance", # رمز كلاسيكي يعبر عن القوة المالية والإدارية
    "SITE_URL": "/",
    # تم التغيير لـ Production عشان السيستم يبان احترافي وجاهز للعمل
    "ENVIRONMENT": "Production", 

    # ألوان الواجهة (Slate Theme - طابع كلاسيكي، رسمي، ومريح لعين المحاسب)
    "COLORS": {
        "primary": {
            "50": "248 250 252",
            "100": "241 245 249",
            "200": "226 232 240",
            "300": "203 213 225",
            "400": "148 163 184",
            "500": "100 116 139",
            "600": "71 85 105",
            "700": "51 65 85",
            "800": "30 41 59",
            "900": "15 23 42",
            "950": "2 6 23",
        },
    },

    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "الرئيسية",
                "separator": True,
                "items": [
                    {
                        "title": "لوحة التحكم",
                        "icon": "dashboard",
                        "link": reverse_lazy("admin:index"),
                        # الرئيسية متاحة للجميع
                        "permission": lambda request: request.user.is_authenticated, 
                    },
                ],
            },
            {
                "title": "المبيعات والعملاء",
                "separator": True,
                "items": [
                    {
                        "title": "العملاء",
                        "icon": "groups",
                        "link": "/admin/partners/partner/?partner_type__exact=customer", 
                        # يظهر للي معاه صلاحية فواتير المبيعات أو السوبر يوزر
                        "permission": lambda request: request.user.has_perm('sales.view_salesinvoice') or request.user.is_superuser,
                    },
                    {
                        "title": "فواتير المبيعات",
                        "icon": "receipt_long",
                        "link": "/admin/sales/salesinvoice/",
                        "permission": lambda request: request.user.has_perm('sales.view_salesinvoice'),
                    },
                ],
            },
            {
                "title": "المشتريات والموردين",
                "separator": True,
                "items": [
                    {
                        "title": "الموردين",
                        "icon": "local_shipping",
                        "link": "/admin/partners/partner/?partner_type__exact=supplier", 
                        # يظهر للي معاه صلاحية فواتير المشتريات أو السوبر يوزر
                        "permission": lambda request: request.user.has_perm('purchases.view_purchaseinvoice') or request.user.is_superuser,
                    },
                    {
                        "title": "فواتير المشتريات",
                        "icon": "shopping_cart",
                        "link": "/admin/purchases/purchaseinvoice/",
                        "permission": lambda request: request.user.has_perm('purchases.view_purchaseinvoice'),
                    },
                ],
            },
            {
                "title": "إدارة المخازن",
                "separator": True,
                "items": [
                    {
                        "title": "المنتجات",
                        "icon": "inventory_2",
                        "link": "/admin/inventory/product/",
                        "permission": lambda request: request.user.has_perm('inventory.view_product'),
                    },
                    {
                        "title": "المخازن",
                        "icon": "warehouse",
                        "link": "/admin/inventory/warehouse/",
                        "permission": lambda request: request.user.has_perm('inventory.view_warehouse'),
                    },
                    {
                        "title": "أرصدة المخزون",
                        "icon": "stacked_bar_chart",
                        "link": "/admin/inventory/stock/",
                        "permission": lambda request: request.user.has_perm('inventory.view_stock'),
                    },
                ],
            },
            {
                "title": "النظام المالي",
                "separator": True,
                "items": [
                    {
                        "title": "شجرة الحسابات",
                        "icon": "account_tree",
                        "link": "/admin/accounting/account/",
                        "permission": lambda request: request.user.has_perm('accounting.view_account'),
                    },
                    {
                        "title": "قيود اليومية",
                        "icon": "menu_book",
                        "link": "/admin/accounting/journalentry/",
                        "permission": lambda request: request.user.has_perm('accounting.view_journalentry'),
                    },
                ],
            },
            {
                "title": "تحليل البيانات", 
                "separator": True,
                "items": [
                    {
                        "title": "التقارير الشاملة",
                        "icon": "analytics",
                        "link": "#", 
                        # التقارير تظهر للمديرين وصلاحيات السوبر يوزر فقط
                        "permission": lambda request: request.user.is_superuser or request.user.groups.filter(name='مدير فرع').exists(),
                    },
                ],
            },
            {
                "title": "إعدادات النظام",
                "separator": True,
                "items": [
                    {
                        "title": "المستخدمين والصلاحيات",
                        "icon": "manage_accounts",
                        "link": "/admin/users/user/",
                        "permission": lambda request: request.user.is_superuser, # السوبر يوزر بس
                    },
                    {
                        "title": "تسلسل الأرقام",
                        "icon": "pin",
                        "link": "/admin/core/sequence/",
                        "permission": lambda request: request.user.is_superuser, # السوبر يوزر بس
                    },
                ],
            },
        ],
    },
    
    # قائمة المستخدم الجانبية العلوية
    "TABS": [
        {
            "models": ["auth.user"],
            "items": [
                {
                    "title": "تغيير كلمة المرور",
                    "link": reverse_lazy("admin:password_change"),
                },
            ],
        },
    ],
}

GRAPH_MODELS = {
    'all_applications': True,
    'group_models': True,
}