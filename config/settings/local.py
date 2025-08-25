from .base import *
from config.env import env
import oracledb

ALLOWED_HOSTS = ['*']
DEBUG = env.bool('DJANGO_DEBUG', default=True)

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

oracledb.init_oracle_client(lib_dir=env('ORACLE_INSTANT_CLIENT_PATH'))
DATABASES = {
    'default': {
        'ENGINE': env('DATABASE_BACKEND'),
        'NAME': env('DATABASE_NAME'),
        'USER': env('DATABASE_USER'),
        'PASSWORD': env('DATABASE_PASS'),
        'HOST': env('DATABASE_HOST'),
        'PORT': env('DATABASE_PORT')
    }
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

if EMAIL_BACKEND == "django.core.mail.backends.filebased.EmailBackend":
    EMAIL_FILE_PATH = "media/emails"  # change this to a proper location
else:
    print("==================== USING LIVE EMAIL ==================")