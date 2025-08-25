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