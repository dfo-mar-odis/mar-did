from .base import *
from config.env import env
import oracledb

ALLOWED_HOSTS = ['*']
DEBUG = env.bool('DJANGO_DEBUG', default=True)

# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

instant_client = os.getenv('ORACLE_INSTANT_CLIENT_PATH', None)
if instant_client:
    oracledb.init_oracle_client(lib_dir=instant_client)

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DATABASE_BACKEND'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASS'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT')
    }
}

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.getenv('MEDIA_DIR', BASE_DIR / 'media')
MEDIA_IN = os.path.join(MEDIA_ROOT, 'IN')
MEDIA_OUT = os.path.join(MEDIA_ROOT, 'OUT')

MEDIA_IN = os.getenv('MEDIA_IN', MEDIA_IN)
MEDIA_OUT = os.getenv('MEDIA_OUT', MEDIA_OUT)

if not os.path.exists(MEDIA_IN):
    os.makedirs(MEDIA_IN)

if not os.path.exists(MEDIA_OUT):
    os.makedirs(MEDIA_OUT)

if EMAIL_BACKEND == "django.core.mail.backends.filebased.EmailBackend":
    EMAIL_FILE_PATH = "media/emails"  # change this to a proper location
else:
    print("==================== USING LIVE EMAIL ==================")