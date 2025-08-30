from .base import *
from config.env import env

ALLOWED_HOSTS = ['ci-bio-mar-did-1']
DEBUG = env.bool('DJANGO_DEBUG', default=False)

AZURE_AUTH = {}
AUTHENTICATION_BACKENDS = (
    'azure_auth.backends.AzureBackend',
    'django.contrib.auth.backends.ModelBackend',
)

INSTALLED_APPS += [
    'azure_auth',
]

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