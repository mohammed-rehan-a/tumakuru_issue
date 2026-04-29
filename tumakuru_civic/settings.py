"""
Tumakuru City - Public Issue Reporting System
Django Settings
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
load_dotenv(os.path.join(BASE_DIR, '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'tumakuru-civic-secret-key-change-in-production-2024')

DEBUG = os.getenv('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'widget_tweaks',
    'rest_framework',
    'accounts',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = 'tumakuru_civic.urls'

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

WSGI_APPLICATION = 'tumakuru_civic.wsgi.application'

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR}/db.sqlite3',
        conn_max_age=600
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = False

LANGUAGES = (
    ('en', 'English'),
    ('kn', 'Kannada'),
)

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Points configuration
POINTS_PER_REPORT = 5
POINTS_FOR_CERTIFICATE = 100

# City name
CITY_NAME = "Tumakuru"
CITY_FULL_NAME = "Tumakuru City Corporation"
CITY_STATE = "Karnataka"

# ─────────────────────────────────────────────────
# EMAIL CONFIGURATION (Gmail SMTP)
# ─────────────────────────────────────────────────
# Step 1: Enable 2-Step Verification on your Gmail
# Step 2: Go to Google Account → Security → App Passwords
# Step 3: Create App Password for "Mail" → copy 16-char password
# Step 4: Paste below

EMAIL_BACKEND        = 'django.core.mail.backends.console.EmailBackend' if os.getenv('EMAIL_DEBUG_CONSOLE', 'False') == 'True' else 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST           = 'smtp.gmail.com'
EMAIL_PORT           = 587
EMAIL_USE_TLS        = True
EMAIL_HOST_USER      = os.getenv('EMAIL_HOST_USER', 'tumakurucity@gmail.com')      # ← Change this
EMAIL_HOST_PASSWORD  = os.getenv('EMAIL_HOST_PASSWORD', 'wotz lymy yjzb opxx')    # ← 16-char App Password
DEFAULT_FROM_EMAIL   = os.getenv('DEFAULT_FROM_EMAIL', 'Tumakuru City Corporation <tumakurucity@gmail.com>')

# Set to True to test without sending real emails (prints to console)
EMAIL_DEBUG_CONSOLE  = os.getenv('EMAIL_DEBUG_CONSOLE', 'False') == 'True'   # Set True during development

# ─────────────────────────────────────────────────
# SMS CONFIGURATION (Fast2SMS — Free Indian API)
# ─────────────────────────────────────────────────
# 1. Register free at https://www.fast2sms.com
# 2. Go to Dev API → copy your API key
# 3. Paste it below

FAST2SMS_API_KEY = os.getenv('FAST2SMS_API_KEY', 'Nlgj9dSIsM61DEtyzTeZxU0P3VcYCv2GX8OwJbhkrnoqKpQL7moyz3nbs05kZep2EV8hOKifTa4dtqMW')   # ← Change this

# SendGrid API Configuration (for reliable email delivery on Render)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', 'VBA79WJ95WPEXVWY2U1YE523')

# ─────────────────────────────────────────────────
# SITE URL (for links in emails)
# ─────────────────────────────────────────────────
SITE_URL = os.getenv('SITE_URL', 'http://127.0.0.1:8000')   # Use environment variable for production

# ─────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'reports.notifications': {
            'handlers' : ['console'],
            'level'    : 'INFO',
            'propagate': False,
        },
    },
}

AUTHENTICATION_BACKENDS = [
    'accounts.backends.CustomAuthBackend',
    'django.contrib.auth.backends.ModelBackend',
]
