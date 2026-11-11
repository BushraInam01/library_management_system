
"""
Django settings for config project.
"""

from pathlib import Path
from decimal import Decimal
import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


# --------------------------------------------------
# BASE DIRECTORY AND ENVIRONMENT
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    return os.getenv(name, str(default)).lower() in (
        'true', '1', 'yes', 'on'
    )


# --------------------------------------------------
# SECURITY AND SECRET KEY
# --------------------------------------------------

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ImproperlyConfigured(
        'DJANGO_SECRET_KEY is missing from environment variables.'
    )

DEBUG = env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        'DJANGO_ALLOWED_HOSTS',
        '127.0.0.1,localhost'
    ).split(',')
    if host.strip()
]


# --------------------------------------------------
# APPLICATION DEFINITION
# --------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'import_export',

    # Local apps
    'accounts',
    'catalog',
    'borrowing',
    'reservations',
    'fines',
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --------------------------------------------------
# PASSWORD VALIDATION
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# --------------------------------------------------
# INTERNATIONALIZATION
# --------------------------------------------------

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Karachi'

USE_I18N = True

USE_TZ = True

# --------------------------------------------------
# LIBRARY FINE CONFIGURATION
# --------------------------------------------------


FINE_RATE_PER_DAY = Decimal('50.00')


# --------------------------------------------------
# STATIC AND MEDIA FILES
# --------------------------------------------------

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = 'media/'

MEDIA_ROOT = BASE_DIR / 'media'


# --------------------------------------------------
# EMAIL CONFIGURATION - DJANGO 6.1 MAILERS
# --------------------------------------------------

if DEBUG:

    # Development: emails appear in the terminal.
    MAILERS = {
        'default': {
            'BACKEND': (
                'django.core.mail.backends.console.EmailBackend'
            ),
        },
    }

else:

    # Production: use a real SMTP email server.
    smtp_host = os.getenv('DJANGO_EMAIL_HOST')
    smtp_username = os.getenv('DJANGO_EMAIL_USERNAME')
    smtp_password = os.getenv('DJANGO_EMAIL_PASSWORD')

    if not all([smtp_host, smtp_username, smtp_password]):
        raise ImproperlyConfigured(
            'Production email settings are incomplete. '
            'Set DJANGO_EMAIL_HOST, DJANGO_EMAIL_USERNAME '
            'and DJANGO_EMAIL_PASSWORD.'
        )

    MAILERS = {
        'default': {
            'BACKEND': (
                'django.core.mail.backends.smtp.EmailBackend'
            ),
            'OPTIONS': {
                'host': smtp_host,
                'port': int(
                    os.getenv('DJANGO_EMAIL_PORT', '587')
                ),
                'username': smtp_username,
                'password': smtp_password,
                'use_tls': env_bool(
                    'DJANGO_EMAIL_USE_TLS',
                    True
                ),
                'timeout': 10,
            },
        },
    }

DEFAULT_FROM_EMAIL = os.getenv(
    'DJANGO_DEFAULT_FROM_EMAIL',
    'Library Management <library@example.com>'
)


# --------------------------------------------------
# CUSTOM USER MODEL
# --------------------------------------------------

AUTH_USER_MODEL = 'accounts.User'


# --------------------------------------------------
# AUTHENTICATION URLS
# --------------------------------------------------

LOGIN_URL = 'accounts:login'

LOGIN_REDIRECT_URL = 'accounts:dashboard'

LOGOUT_REDIRECT_URL = 'accounts:login'


# --------------------------------------------------
# PRODUCTION SECURITY SETTINGS
# --------------------------------------------------

SECURE_SSL_REDIRECT = not DEBUG

SESSION_COOKIE_SECURE = not DEBUG

CSRF_COOKIE_SECURE = not DEBUG

SECURE_HSTS_SECONDS = int(
    os.getenv(
        'DJANGO_SECURE_HSTS_SECONDS',
        '0' if DEBUG else '31536000'
    )
)

SECURE_HSTS_INCLUDE_SUBDOMAINS = False

SECURE_HSTS_PRELOAD = False

SECURE_CONTENT_TYPE_NOSNIFF = True


# --------------------------------------------------
# DEFAULT PRIMARY KEY
# --------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
