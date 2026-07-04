

from pathlib import Path
import os
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Logs directory yaratish
LOGS_DIR = BASE_DIR / 'logs'
LOGS_DIR.mkdir(exist_ok=True)


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')

# Payme Configuration
PAYME_MERCHANT_ID = config('PAYME_MERCHANT_ID', default='')
PAYME_KEY = config('PAYME_KEY', default='')
PAYME_ACCOUNT_FIELD = config('PAYME_ACCOUNT_FIELD', default='order_id')

# Payme IP whitelist - vergul bilan ajratilgan IP manzillar ro'yxati
# Production uchun: 185.178.51.131,185.178.51.132,195.158.31.134,195.158.31.10
# Development uchun bo'sh qoldirish mumkin (barcha IP'larga ruxsat)
PAYME_ALLOWED_IPS_RAW = config('PAYME_ALLOWED_IPS', default='')
PAYME_ALLOWED_IPS = [ip.strip() for ip in PAYME_ALLOWED_IPS_RAW.split(',') if ip.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    #packages
    'rest_framework',
    'drf_spectacular',  # Swagger/OpenAPI documentation

    #apps
    'payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'payments.middleware.PaymeRequestLoggingMiddleware',  # Payme so'rovlarini loglash
]

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    # Swagger/OpenAPI schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# DRF Spectacular (Swagger) settings
SPECTACULAR_SETTINGS = {
    'TITLE': 'Payme Backend API',
    'DESCRIPTION': '''
# Payme Merchant API Integration

Backend xizmati Telegram Mini App uchun Payme to'lov tizimi bilan integratsiya.

## 🔐 Authentication

### Webhook Endpoint
Payme webhook endpoint'lari Basic Authentication talab qiladi:

```
Authorization: Basic base64(Paycom:YOUR_PAYME_KEY)
```

### IP Whitelist
Production muhitda faqat Payme serverlaridan kelgan so'rovlar qabul qilinadi:
- 185.178.51.131
- 185.178.51.132
- 195.158.31.134
- 195.158.31.10

## 📊 Workflow

1. **Order yaratish** - Telegram Mini App orqali order yaratiladi (Firestore)
2. **To'lov havolasi** - `/api/payments/create-link/` endpoint'idan checkout URL olinadi
3. **To'lov** - Foydalanuvchi Payme'da to'lovni amalga oshiradi
4. **Webhook** - Payme webhook'lar yuboradi va order statusi yangilanadi

## 🔗 Useful Links

- [Payme Documentation](https://developer.help.paycom.uz/)
- [Firebase Firestore](https://firebase.google.com/docs/firestore)
- [GitHub Repository](https://github.com/your-repo)
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'TAGS': [
        {
            'name': 'Payments',
            'description': 'To\'lov havolasini yaratish va boshqarish'
        },
        {
            'name': 'Payme Webhook',
            'description': 'Payme Merchant API webhook (JSON-RPC 2.0)'
        },
    ],
    'CONTACT': {
        'name': 'Payme Backend Team',
        'email': 'support@yourcompany.com',
    },
    'LICENSE': {
        'name': 'MIT License',
    },
    'SERVERS': [
        {
            'url': 'http://localhost:8000',
            'description': 'Development server'
        },
        {
            'url': 'https://api.yourcompany.com',
            'description': 'Production server'
        },
    ],
    # Schema settings
    'SCHEMA_PATH_PREFIX': r'/api/',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
}

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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

# Default primary key field type
# https://docs.djangoproject.com/en/6.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {module} - {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'payme_backend.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'payments': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}



