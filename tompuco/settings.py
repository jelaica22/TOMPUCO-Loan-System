"""
Django settings for tompuco project.
"""

from pathlib import Path
import os
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # OTP apps
    'django_otp',
    'django_otp.plugins.otp_totp',
    'django_otp.plugins.otp_static',
    'channels',
    # Your apps
    'main',
    'staff',
    'cashier',
    'committee',
    'manager',
    'admin_panel',
    'reports',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django_otp.middleware.OTPMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'main.middleware.VerificationMiddleware',
]

# Unverified member restrictions
UNVERIFIED_MAX_LOAN_AMOUNT = 10000
UNVERIFIED_MAX_ACTIVE_LOANS = 0

ROOT_URLCONF = 'tompuco.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'admin_panel.context_processors.admin_profile',
                'main.context_processors.staff_profile_context',
                'manager.context_processors.manager_profile',
                'main.context_processors.member_profile',
                'cashier.context_processors.cashier_profile',
            ],
        },
    },
]

WSGI_APPLICATION = 'tompuco.wsgi.application'  # Keep this for HTTP
ASGI_APPLICATION = 'tompuco.asgi.application'  # ADD THIS for WebSockets


# Channel layers for real-time notifications
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',  # For development
        # For production, use Redis:
        # 'BACKEND': 'channels_redis.core.RedisChannelLayer',
        # 'CONFIG': {
        #     "hosts": [('127.0.0.1', 6379)],
        # },
    },
}

# ============================================
# DATABASE - POSTGRESQL FOR RENDER
# ============================================

# Check if running on Render (has DATABASE_URL)
if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600, ssl_require=True)
    }
# Check if running on PythonAnywhere
elif 'PYTHONANYWHERE_DOMAIN' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'tompuco92$default'),
            'USER': os.environ.get('DB_USER', 'tompuco92'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', 'tompuco92.mysql.pythonanywhere-services.com'),
            'PORT': '3306',
        }
    }
else:
    # Local development with SQLite (simple and works everywhere)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Manila'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise for static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Session settings
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 3600  # 1 hour

# Staff settings
STAFF_SESSION_TIMEOUT = 1800  # 30 minutes
PENALTY_START_DAYS = 360
PENALTY_RATE = 0.02  # 2% per month

# Email backend
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOGIN_REDIRECT_URL = '/dashboard/redirect/'