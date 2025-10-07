from pathlib import Path
import os

# ------------------------------
# BASE_DIR
# ------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------------
# SEGURANÇA
# ------------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-6=2wbklzetya@d6mvys#4$n6)4l=ce5i!q!u&fv5$6d4jmwy42')
DEBUG = True
ALLOWED_HOSTS = []

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
    'chamados.apps.ChamadosConfig',  # app principal
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

# ------------------------------
# AUTENTICAÇÃO CUSTOMIZADA
# ------------------------------
AUTH_USER_MODEL = 'chamados.CustomUser'

# ------------------------------
# BANCO DE DADOS - POSTGRESQL
# ------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'sistema_chamados',
        'USER': 'postgres',
        'PASSWORD': 'admininventory',
        'HOST': 'localhost',
        'PORT': '5432',
        'OPTIONS': {
            'client_encoding': 'UTF8',
        }
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
# ------------------------------
# DEFAULT AUTO FIELD
# ------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

