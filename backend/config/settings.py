from datetime import timedelta
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.join(BASE_DIR, 'apps'))

# -----------------------------------------------------------------------------
# Security / Environment
# -----------------------------------------------------------------------------
SECRET_KEY = os.getenv('SECRET_KEY', 'unsafe-secret-key-for-dev')
DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
    'https://*.ngrok-free.dev',
]

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = 'login'

# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Unfold Admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",
    #django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',
    'corsheaders',
    "rest_framework_simplejwt",
    "drf_spectacular",
    "django_filters",

    # My apps
    'apps.core',
    'apps.users',
    'apps.inventory',
    'apps.partners',
    'apps.purchases',
    'apps.accounting',
    'apps.sales',
    'apps.ai_assistant',
]

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # لو هتستخدم LoginRequiredMiddleware خليك واعي إنه قد يؤثر على الـ APIs
    'django.contrib.auth.middleware.LoginRequiredMiddleware',

    'django.contrib.messages.middleware.MessageMiddleware',

    # آخر واحد حتى يكون user جاهز
    'apps.core.middleware.ThreadLocalMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------
load_dotenv(os.path.join(BASE_DIR, '.env'))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'erp_db'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# -----------------------------------------------------------------------------
# Password validation
# -----------------------------------------------------------------------------
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

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------------------------------------------------------
# Static files
# -----------------------------------------------------------------------------
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
]
CORS_ALLOW_CREDENTIALS = True

# -----------------------------------------------------------------------------
# Auth / Cache / API
# -----------------------------------------------------------------------------
AUTH_USER_MODEL = 'users.User'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'erp_cache_table',
    }
}


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}   

SPECTACULAR_SETTINGS = {
    "TITLE": "ERP System API",
    "DESCRIPTION": "ERP Backend APIs for Sales, Purchases, Inventory and Accounting",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "TAGS": [
        {"name": "Auth", "description": "Authentication APIs"},
        {"name": "Partners", "description": "Customers and suppliers APIs"},
        {"name": "Inventory - Master Data", "description": "Units, products, and warehouses"},
        {"name": "Inventory - Transactions", "description": "Stock transactions and stock movements"},
        {"name": "Inventory - Reports", "description": "Stock balances and inventory inquiries"},
        {"name": "Sales Invoices", "description": "Sales invoices operations"},
        {"name": "Sales Invoice Items", "description": "Sales invoice items operations"},
        {"name": "Purchase Invoices", "description": "Purchase invoices operations"},
        {"name": "Purchase Invoice Items", "description": "Purchase invoice items operations"},
    ],
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "displayOperationId": False,
        "defaultModelsExpandDepth": 1,
        "defaultModelExpandDepth": 1,
        "displayRequestDuration": True,
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -----------------------------------------------------------------------------
# Sidebar permissions helpers
# -----------------------------------------------------------------------------
def is_auth(request):
    return request.user.is_authenticated


def is_superuser(request):
    return request.user.is_authenticated and request.user.is_superuser


def has_perm(request, perm_name):
    return request.user.is_authenticated and request.user.has_perm(perm_name)


def is_branch_manager(request):
    return request.user.is_authenticated and request.user.groups.filter(name='مدير فرع').exists()


# -----------------------------------------------------------------------------
# Unfold Admin Settings
# -----------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "ERP System | Enterprise",
    "SITE_HEADER": "نظام الإدارة المتكامل",
    "SITE_SYMBOL": "account_balance",
    "SITE_URL": "/",
    "ENVIRONMENT": os.getenv("APP_ENV", "Production"),

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
                        "permission": is_auth,
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
                        "permission": lambda request: has_perm(request, 'sales.view_salesinvoice') or is_superuser(request),
                    },
                    {
                        "title": "فواتير المبيعات",
                        "icon": "receipt_long",
                        "link": "/admin/sales/salesinvoice/",
                        "permission": lambda request: has_perm(request, 'sales.view_salesinvoice') or is_superuser(request),
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
                        "permission": lambda request: has_perm(request, 'purchases.view_purchaseinvoice') or is_superuser(request),
                    },
                    {
                        "title": "فواتير المشتريات",
                        "icon": "shopping_cart",
                        "link": "/admin/purchases/purchaseinvoice/",
                        "permission": lambda request: has_perm(request, 'purchases.view_purchaseinvoice') or is_superuser(request),
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
                        "permission": lambda request: has_perm(request, 'inventory.view_product') or is_superuser(request),
                    },
                    {
                        "title": "المخازن",
                        "icon": "warehouse",
                        "link": "/admin/inventory/warehouse/",
                        "permission": lambda request: has_perm(request, 'inventory.view_warehouse') or is_superuser(request),
                    },
                    {
                        "title": "أرصدة المخزون",
                        "icon": "stacked_bar_chart",
                        "link": "/admin/inventory/stockbalance/",
                        "permission": lambda request: has_perm(request, 'inventory.view_stockbalance') or is_superuser(request),
                    },
                    {
                        "title": "الحركات المخزنية",
                        "icon": "swap_horiz",
                        "link": "/admin/inventory/stocktransaction/",
                        "permission": lambda request: has_perm(request, 'inventory.view_stocktransaction') or is_superuser(request),
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
                        "permission": lambda request: has_perm(request, 'accounting.view_account') or is_superuser(request),
                    },
                    {
                        "title": "دفاتر اليومية",
                        "icon": "book",
                        "link": "/admin/accounting/journal/",
                        "permission": lambda request: has_perm(request, 'accounting.view_journal') or is_superuser(request),
                    },
                    {
                        "title": "قيود اليومية",
                        "icon": "menu_book",
                        "link": "/admin/accounting/journalentry/",
                        "permission": lambda request: has_perm(request, 'accounting.view_journalentry') or is_superuser(request),
                    },
                    {
                        "title": "سندات القبض والصرف",
                        "icon": "payments",
                        "link": "/admin/accounting/payment/",
                        "permission": lambda request: has_perm(request, 'accounting.view_payment') or is_superuser(request),
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
                        "permission": lambda request: is_superuser(request) or is_branch_manager(request),
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
                        "permission": is_superuser,
                    },
                    {
                        "title": "تسلسل الأرقام",
                        "icon": "pin",
                        "link": "/admin/core/sequence/",
                        "permission": is_superuser,
                    },
                    {
                        "title": "الشركات والفروع",
                        "icon": "apartment",
                        "link": "/admin/core/company/",
                        "permission": is_superuser,
                    },
                ],
            },
        ],
    },

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
