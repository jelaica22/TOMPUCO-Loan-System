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
DEBUG = os.environ.get('DEBUG', 'False') == 'True'  # Default to False for production safety

# ALLOWED_HOSTS - Production ready
ALLOWED_HOSTS = [
    'tompuco-loan-system.onrender.com',
    'localhost',
    '127.0.0.1',
]

# Add localhost for development only
if DEBUG:
    ALLOWED_HOSTS.extend(['0.0.0.0', '*'])

# CSRF Trusted Origins
CSRF_TRUSTED_ORIGINS = [
    'https://tompuco-loan-system.onrender.com',
    'https://*.onrender.com',
]

if DEBUG:
    CSRF_TRUSTED_ORIGINS.extend([
        'http://localhost:8000',
        'http://127.0.0.1:8000',
    ])

# ============================================
# reCAPTCHA Configuration - Production Ready
# ============================================
# Read from environment variables (set on Render)
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '')
RECAPTCHA_PUBLIC_KEY = RECAPTCHA_SITE_KEY
RECAPTCHA_PRIVATE_KEY = RECAPTCHA_SECRET_KEY

# ⚠️ IMPORTANT: Only use test keys in development, NEVER in production
# The test keys will show "This reCAPTCHA is for testing purposes only"
if DEBUG and not RECAPTCHA_SITE_KEY:
    # Use test keys for local development only
    RECAPTCHA_SITE_KEY = '6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
    RECAPTCHA_SECRET_KEY = '6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
    RECAPTCHA_PUBLIC_KEY = RECAPTCHA_SITE_KEY
    RECAPTCHA_PRIVATE_KEY = RECAPTCHA_SECRET_KEY
    print("⚠️ Using Google test reCAPTCHA keys for DEVELOPMENT only")
elif not DEBUG and not RECAPTCHA_SITE_KEY:
    # This should NEVER happen in production - warn in logs
    print("❌ ERROR: reCAPTCHA keys not set in production environment!")

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
    # reCAPTCHA
    'django_recaptcha',
    'captcha',
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
]

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
                'main.context_processors.recaptcha_site_key',
            ],
        },
    },
]

WSGI_APPLICATION = 'tompuco.wsgi.application'
ASGI_APPLICATION = 'tompuco.asgi.application'

# Channel layers for real-time notifications
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}

# ============================================
# DATABASE - PRODUCTION READY
# ============================================

if os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': dj_database_url.config(
            conn_max_age=600,
            ssl_require=True
        )
    }
elif os.environ.get('PYTHONANYWHERE_DOMAIN'):
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
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/redirect/'
LOGOUT_REDIRECT_URL = '/login/'

# Session settings for "Remember Me" functionality
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 2592000  # 30 days in seconds
SESSION_SAVE_EVERY_REQUEST = True

# Staff settings
STAFF_SESSION_TIMEOUT = 1800
PENALTY_START_DAYS = 361  # Penalty starts at DAY 361 (after 360 days grace period)
PENALTY_RATE = 0.02  # 2% per month penalty

# Email backend (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Unverified member restrictions
UNVERIFIED_MAX_LOAN_AMOUNT = 10000
UNVERIFIED_MAX_ACTIVE_LOANS = 0

# ============================================
# SECURITY SETTINGS FOR PRODUCTION
# ============================================
if not DEBUG:
    # HTTPS settings
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

    # Cookie security
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # Additional security headers
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

    # HSTS (HTTP Strict Transport Security)
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    # CSRF and Session
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================
# DEBUG PRINT (REMOVE IN PRODUCTION)
# ============================================
# Only print in development to avoid log clutter
if DEBUG:
    print(f"✅ reCAPTCHA Site Key: {'✓ Loaded' if RECAPTCHA_SITE_KEY else '✗ NOT SET'}")
    print(f"🔧 DEBUG mode: {DEBUG}")