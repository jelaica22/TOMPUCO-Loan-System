"""
Django settings for tompuco project.
"""

from pathlib import Path
import os
import dj_database_url
import socket
import sys

# ============================================
# FORCE IPv4 FOR ALL CONNECTIONS
# ============================================
# This fixes the "Network is unreachable" error with Supabase
def force_ipv4():
    """Force socket connections to use IPv4 only"""
    try:
        # Get the original getaddrinfo
        original_getaddrinfo = socket.getaddrinfo
        
        def ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
            # Force IPv4 for database connections
            if 'supabase.co' in str(host) or 'db.' in str(host):
                # Only return IPv4 addresses
                try:
                    result = original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
                    if result:
                        return result
                except:
                    pass
            # For other connections, try default
            return original_getaddrinfo(host, port, family, type, proto, flags)
        
        socket.getaddrinfo = ipv4_getaddrinfo
        print("✅ IPv4 forced for socket connections")
    except Exception as e:
        print(f"⚠️  Could not force IPv4: {e}")

# Apply IPv4 fix before any database connections
force_ipv4()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here-change-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

# ALLOWED_HOSTS - Production ready
ALLOWED_HOSTS = [
    'tompuco-loan-system.onrender.com',
    'localhost',
    '127.0.0.1',
]

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
# reCAPTCHA Configuration
# ============================================
RECAPTCHA_SITE_KEY = os.environ.get('RECAPTCHA_SITE_KEY', '6LelneksAAAAAJ84pRMje7M5YSDRpm2xXPuiJuat')
RECAPTCHA_SECRET_KEY = os.environ.get('RECAPTCHA_SECRET_KEY', '6LelneksAAAAAKP6CjXA_y-fuAFwfzw61hx9VSHJ')
RECAPTCHA_PUBLIC_KEY = RECAPTCHA_SITE_KEY
RECAPTCHA_PRIVATE_KEY = RECAPTCHA_SECRET_KEY

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
# DATABASE CONFIGURATION
# ============================================

def get_db_url():
    """Get database URL with proper IPv4 handling"""
    db_url = os.environ.get('DATABASE_URL', '')
    if db_url:
        # Force IPv4 in the connection string
        if 'supabase.co' in db_url:
            # Replace with IPv4-specific settings
            if 'connect_timeout' not in db_url:
                db_url += '&connect_timeout=10'
            if 'keepalives' not in db_url:
                db_url += '&keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=3'
    return db_url

if os.environ.get('DATABASE_URL'):
    db_url = get_db_url()
    DATABASES = {
        'default': dj_database_url.config(
            default=db_url,
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
    # Local development - PostgreSQL
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'tompuco_db',
            'USER': 'tompuco_db_user',
            'PASSWORD': 'user_123',
            'HOST': 'localhost',
            'PORT': '5432',
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
PENALTY_START_DAYS = 361
PENALTY_RATE = 0.02

# Email backend (for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Unverified member restrictions
UNVERIFIED_MAX_LOAN_AMOUNT = 10000
UNVERIFIED_MAX_ACTIVE_LOANS = 0

# ============================================
# SECURITY SETTINGS FOR PRODUCTION
# ============================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SAMESITE = 'Lax'