from .base import *
from config.env import env

ALLOWED_HOSTS = ['ci-bio-mar-did-1']
DEBUG = env.bool('DJANGO_DEBUG', default=False)