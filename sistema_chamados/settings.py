from pathlib import Path
from decouple import config
import dj_database_url
import os
import ssl
# ------------------------------
# BASE_DIR
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# SEGURANÇA
# ------------------------------
SECRET_KEY = config('SECRET_KEY', default='django-insecure-6=2wbklzetya@d6mvys#4$n6)4l=ce5i!q!u&fv5$6d4jmwy42')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = ['sistema-chamados-1-tp25.onrender.com', '127.0.0.1', 'localhost']

# ------------------------------
# LOGIN
# ------------------------------
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# ------------------------------
# APPS INSTALADOS
# ------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chamados.apps.ChamadosConfig',
    'channels',
]

# ------------------------------
# MIDDLEWARE
# ------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# ------------------------------
# URLS
# ------------------------------
ROOT_URLCONF = 'sistema_chamados.urls'

# ------------------------------
# TEMPLATES
# ------------------------------
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

# ------------------------------
# WSGI
# ------------------------------
WSGI_APPLICATION = 'sistema_chamados.wsgi.application'
ASGI_APPLICATION = 'sistema_chamados.asgi.application'

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}
# ------------------------------
# AUTENTICAÇÃO CUSTOMIZADA
# ------------------------------
AUTH_USER_MODEL = 'chamados.CustomUser'

# ------------------------------
# BANCO DE DADOS - POSTGRESQL
# ------------------------------
# Banco de dados
if os.environ.get('RENDER') == 'true':
    # Banco do Render
    DATABASES = {
        'default': dj_database_url.parse(config('DATABASE_URL'), conn_max_age=600)
    }
else:
    # Banco local
    DATABASES = {
        'default': {
            'ENGINE': config('DB_ENGINE'),
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT'),
            'OPTIONS': {'client_encoding': 'UTF8'},
        }
    }


# ------------------------------
# VALIDAÇÃO DE SENHA
# ------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ------------------------------
# LOCALIZAÇÃO
# ------------------------------
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# ------------------------------
# STATIC FILES
# ------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']  # criar pasta static para evitar warnings
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
# ------------------------------
# DEFAULT AUTO FIELD
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

