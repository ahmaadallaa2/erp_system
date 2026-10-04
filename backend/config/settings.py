import os
import sys
from datetime import timedelta
from pathlib import Path

from django.urls import reverse_lazy
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

if os.getenv('SKIP_DOTENV') != 'True':
    load_dotenv(BASE_DIR / '.env')


# -----------------------------------------------------------------------------
# Security / Environment
# -----------------------------------------------------------------------------
def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {'1', 'true', 'yes', 'on'}


def env_int(name, default=0):
    value = os.getenv(name)
    if value in (None, ''):
        return default
    return int(value)


def env_list(name, default=None):
    value = os.getenv(name)
    if value is None:
        return list(default or [])
    return [item.strip() for item in value.split(',') if item.strip()]


DEBUG = env_bool('DEBUG', default=False)
RUNNING_TESTS = 'test' in sys.argv

APP_ENV = os.getenv('APP_ENV', 'Development' if DEBUG else 'Production')
if DEBUG and APP_ENV.strip().lower() == 'production':
    raise RuntimeError('DEBUG must be False when APP_ENV=Production.')

SECRET_KEY = os.getenv('SECRET_KEY', '')
if DEBUG:
    SECRET_KEY = SECRET_KEY or 'unsafe-local-development-secret-key'
elif not SECRET_KEY:
    raise RuntimeError('SECRET_KEY environment variable is required when DEBUG=False.')
elif len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5 or SECRET_KEY.startswith('django-insecure-'):
    raise RuntimeError(
        'SECRET_KEY is too weak for DEBUG=False: use at least 50 random characters '
        '(e.g. python -c "from django.core.management.utils import get_random_secret_key; '
        'print(get_random_secret_key())").'
    )

ALLOWED_HOSTS = env_list(
    'ALLOWED_HOSTS',
    default=['127.0.0.1', 'localhost'] if DEBUG else [],
)
if not DEBUG and not ALLOWED_HOSTS:
    raise RuntimeError('ALLOWED_HOSTS environment variable is required when DEBUG=False.')
if not DEBUG and '*' in ALLOWED_HOSTS:
    raise RuntimeError('ALLOWED_HOSTS cannot include * when DEBUG=False.')

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS', default=[
    'http://localhost:5173',
    'https://*.ngrok-free.app',
    'https://*.ngrok.io',
    'https://*.ngrok-free.dev',
]) if DEBUG else env_list('CSRF_TRUSTED_ORIGINS')

CORS_ALLOWED_ORIGINS = env_list(
    'CORS_ALLOWED_ORIGINS',
    default=['http://localhost:5173'] if DEBUG else [],
)
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL_ORIGINS', default=False)
if not DEBUG and CORS_ALLOW_ALL_ORIGINS:
    raise RuntimeError('CORS_ALLOW_ALL_ORIGINS cannot be enabled when DEBUG=False.')
# The SPA authenticates with a Bearer header, so cross-origin cookies are not needed.
CORS_ALLOW_CREDENTIALS = env_bool('CORS_ALLOW_CREDENTIALS', default=False)

SECURE_SSL_REDIRECT = env_bool('SECURE_SSL_REDIRECT', default=not DEBUG and not RUNNING_TESTS)
# Platform health checks probe the container over plain HTTP.
SECURE_REDIRECT_EXEMPT = [r'^health/$']
SESSION_COOKIE_SECURE = True if not DEBUG else env_bool('SESSION_COOKIE_SECURE', default=False)
CSRF_COOKIE_SECURE = True if not DEBUG else env_bool('CSRF_COOKIE_SECURE', default=False)
SESSION_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = env_int('SECURE_HSTS_SECONDS', default=31536000 if not DEBUG else 0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    'SECURE_HSTS_INCLUDE_SUBDOMAINS',
    default=not DEBUG,
)
SECURE_HSTS_PRELOAD = env_bool('SECURE_HSTS_PRELOAD', default=False)
USE_X_FORWARDED_PROTO = env_bool('USE_X_FORWARDED_PROTO', default=not DEBUG)
if USE_X_FORWARDED_PROTO:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
X_FRAME_OPTIONS = os.getenv('X_FRAME_OPTIONS', 'DENY').upper()
if X_FRAME_OPTIONS not in {'DENY', 'SAMEORIGIN'}:
    raise RuntimeError('X_FRAME_OPTIONS must be DENY or SAMEORIGIN.')
SECURE_CONTENT_TYPE_NOSNIFF = env_bool('SECURE_CONTENT_TYPE_NOSNIFF', default=True)
SECURE_REFERRER_POLICY = 'same-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'

API_DOCS_ENABLED = env_bool('API_DOCS_ENABLED', default=True)
AI_DOCUMENT_MAX_UPLOAD_MB = env_int('AI_DOCUMENT_MAX_UPLOAD_MB', default=20)

LOGIN_URL = '/admin/login/'
LOGIN_REDIRECT_URL = '/admin/'
LOGOUT_REDIRECT_URL = '/admin/login/'

# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------
INSTALLED_APPS = [
    # Unfold Admin
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "unfold.contrib.inlines",

    # Django apps
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

    # Project apps
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Must run after AuthenticationMiddleware so request.user is populated.
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
LOCAL_DB_DEFAULTS = {
    'DB_NAME': 'erp_db',
    'DB_USER': 'postgres',
    'DB_PASSWORD': '',
    'DB_HOST': 'localhost',
}
if not DEBUG:
    missing_db_vars = [name for name in LOCAL_DB_DEFAULTS if not os.getenv(name)]
    if missing_db_vars:
        raise RuntimeError(
            'Database environment variables are required when DEBUG=False: '
            + ', '.join(missing_db_vars)
        )

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', LOCAL_DB_DEFAULTS['DB_NAME']),
        'USER': os.getenv('DB_USER', LOCAL_DB_DEFAULTS['DB_USER']),
        'PASSWORD': os.getenv('DB_PASSWORD', LOCAL_DB_DEFAULTS['DB_PASSWORD']),
        'HOST': os.getenv('DB_HOST', LOCAL_DB_DEFAULTS['DB_HOST']),
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
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

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
    "DEFAULT_RENDERER_CLASSES": (
        ("rest_framework.renderers.JSONRenderer", "rest_framework.renderers.BrowsableAPIRenderer")
        if DEBUG
        else ("rest_framework.renderers.JSONRenderer",)
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": os.getenv("AUTH_THROTTLE_RATE", "10/minute"),
    },
    # Number of trusted reverse proxies in front of Django. 0 ignores
    # X-Forwarded-For so clients cannot spoof their IP to dodge throttling.
    "NUM_PROXIES": env_int("NUM_PROXIES", default=0),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "ERP System API",
    "DESCRIPTION": "ERP Backend APIs for Sales, Purchases, Inventory and Accounting",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SERVE_PERMISSIONS": (
        ["rest_framework.permissions.AllowAny"]
        if DEBUG
        else ["rest_framework.permissions.IsAdminUser"]
    ),
    "SERVE_AUTHENTICATION": None if DEBUG else [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
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

# Django's default LOGGING drops request errors when DEBUG=False unless ADMINS
# email is configured; send them to stdout so the platform log captures them.
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "WARNING"),
    },
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}

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
    return request.user.is_authenticated and request.user.groups.filter(name='BranchManager').exists()


def perm_or_superuser(perm_name):
    return lambda request: has_perm(request, perm_name) or is_superuser(request)


def environment_callback(request):
    return [APP_ENV, "danger" if APP_ENV.strip().lower() == "production" else "info"]


# -----------------------------------------------------------------------------
# Unfold Admin Settings
# -----------------------------------------------------------------------------
UNFOLD = {
    "SITE_TITLE": "ERP System | Enterprise",
    "SITE_HEADER": "نظام الإدارة المتكامل",
    "SITE_SYMBOL": "account_balance",
    "SITE_URL": "/",
    "ENVIRONMENT": "config.settings.environment_callback",

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
                        "permission": perm_or_superuser('sales.view_salesinvoice'),
                    },
                    {
                        "title": "فواتير المبيعات",
                        "icon": "receipt_long",
                        "link": "/admin/sales/salesinvoice/",
                        "permission": perm_or_superuser('sales.view_salesinvoice'),
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
                        "permission": perm_or_superuser('purchases.view_purchaseinvoice'),
                    },
                    {
                        "title": "فواتير المشتريات",
                        "icon": "shopping_cart",
                        "link": "/admin/purchases/purchaseinvoice/",
                        "permission": perm_or_superuser('purchases.view_purchaseinvoice'),
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
                        "permission": perm_or_superuser('inventory.view_product'),
                    },
                    {
                        "title": "المخازن",
                        "icon": "warehouse",
                        "link": "/admin/inventory/warehouse/",
                        "permission": perm_or_superuser('inventory.view_warehouse'),
                    },
                    {
                        "title": "أرصدة المخزون",
                        "icon": "stacked_bar_chart",
                        "link": "/admin/inventory/stockbalance/",
                        "permission": perm_or_superuser('inventory.view_stockbalance'),
                    },
                    {
                        "title": "الحركات المخزنية",
                        "icon": "swap_horiz",
                        "link": "/admin/inventory/stocktransaction/",
                        "permission": perm_or_superuser('inventory.view_stocktransaction'),
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
                        "permission": perm_or_superuser('accounting.view_account'),
                    },
                    {
                        "title": "دفاتر اليومية",
                        "icon": "book",
                        "link": "/admin/accounting/journal/",
                        "permission": perm_or_superuser('accounting.view_journal'),
                    },
                    {
                        "title": "قيود اليومية",
                        "icon": "menu_book",
                        "link": "/admin/accounting/journalentry/",
                        "permission": perm_or_superuser('accounting.view_journalentry'),
                    },
                    {
                        "title": "سندات القبض والصرف",
                        "icon": "payments",
                        "link": "/admin/accounting/payment/",
                        "permission": perm_or_superuser('accounting.view_payment'),
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
}
