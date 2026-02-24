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

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    "unfold",  # لازم تكون أول واحدة هنا
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

    # 6. التوثيق (لازم يجي بعد الـ Session عشان يعرف مين اليوزر)
    'django.contrib.auth.middleware.AuthenticationMiddleware',

    # 7. الرسائل المؤقتة
    'django.contrib.messages.middleware.MessageMiddleware',

    # 8. حماية الـ Clickjacking
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # 9. الميدلوير الخاص بينا (آخر واحد عشان يضمن إن الـ Auth خلص واليوزر بقى موجود)
    'apps.core.middleware.ThreadLocalMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
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



# unfold admin settings
UNFOLD = {
    "SITE_TITLE": "ERP System",
    "SITE_HEADER": "إدارة النظام المتكامل",
    "SITE_SYMBOL": "speed", # أيقونة بجانب العنوان (Heroicon name)
    
    # ضبط السايد بار كما طلبت (إظهار الكل تلقائياً)
    "SIDEBAR": {
        "show_search": True, # شريط بحث سريع عن الموديلات
        "show_all_applications": True, 
        "navigation": [], # فارغة ليعتمد على التلقائي
    },

    # ألوان الواجهة (يمكنك تخصيصها لتناسب ذوقك الكلاسيكي)
    "COLORS": {
        "primary": {
            "50": "250 250 250",
            "100": "244 244 245",
            "200": "228 228 231",
            "300": "212 212 216",
            "400": "161 161 170",
            "500": "113 113 122",
            "600": "82 82 91",
            "700": "63 63 70",
            "800": "39 39 42",
            "900": "24 24 27",
            "950": "9 9 11",
        },
    },
}