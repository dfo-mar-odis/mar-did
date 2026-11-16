from .base import *
from config.env import env

ALLOWED_HOSTS = ['*']
DEBUG = env.bool('DJANGO_DEBUG', default=False)

AZURE_AUTH = {}
AUTHENTICATION_BACKENDS = (
    'azure_auth.backends.AzureBackend',
    'django.contrib.auth.backends.ModelBackend',
)

INSTALLED_APPS += [
    'azure_auth',
]

DATABASES = {
    'default': {
        'ENGINE': os.getenv('AUTH_DATABASE_BACKEND', os.getenv('DATABASE_BACKEND')),
        'NAME': os.getenv('AUTH_DATABASE_NAME', os.getenv('DATABASE_NAME')),
        'USER': os.getenv('AUTH_DATABASE_USER', os.getenv('DATABASE_USER')),
        'PASSWORD': os.getenv('AUTH_DATABASE_PASS', os.getenv('DATABASE_PASS')),
        'HOST': os.getenv('AUTH_DATABASE_HOST', os.getenv('DATABASE_HOST')),
        'PORT': os.getenv('AUTH_DATABASE_PORT', os.getenv('DATABASE_PORT'))
    },
    'core': {
        'ENGINE': os.getenv('DATABASE_BACKEND'),
        'NAME': os.getenv('DATABASE_NAME'),
        'USER': os.getenv('DATABASE_USER'),
        'PASSWORD': os.getenv('DATABASE_PASS'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT')
    }
}