import os
from pathlib import Path

# ---------------------------
# Base directory
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------
# Security
# ---------------------------
# SECRET_KEY should be set as environment variable in cPanel Python App
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'unsafe-default-key-for-dev')

DEBUG = False  # Must be False in production

ALLOWED_HOSTS = ['iuiuaa.org', 'www.iuiuaa.org']

# ---------------------------
# Installed apps
# ---------------------------
INSTALLED_APPS = [
    # 'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'iuiuapp',
]

# ---------------------------
# Middleware
# ---------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ---------------------------
# URLs and WSGI
# ---------------------------
ROOT_URLCONF = 'iuiualumni.urls'

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
            ],
        },
    },
]

WSGI_APPLICATION = 'iuiualumni.wsgi.application'

# ---------------------------
# Database (Production MySQL)
# ---------------------------
DATABASES = {
    'default': {
        'ENGINE': 'mysql.connector.django',
        'NAME': 'iuiuaaor_iuiuaa_sitedb',       # Your cPanel DB name
        'USER': 'iuiuaaor_site',         # Your cPanel DB user
        'PASSWORD': 'iuiuAlumni123!',      # Your cPanel DB password
        'HOST': 'localhost',
        'PORT': '3306',
    }
}

# ---------------------------
# Custom User Model
# ---------------------------
AUTH_USER_MODEL = 'iuiuapp.User'

# ---------------------------
# Password validation
# ---------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',},
]

# ---------------------------
# Internationalization
# ---------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Kampala'
USE_I18N = True
USE_TZ = True

# ---------------------------
# Static files
# ---------------------------
STATIC_URL = '/main/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # collectstatic target
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]

# ---------------------------
# Media files
# ---------------------------
MEDIA_URL = '/main/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')





# ---------------------------
# Default primary key field
# ---------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
