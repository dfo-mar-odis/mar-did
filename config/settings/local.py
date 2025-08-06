from .base import *
from config.env import env

ALLOWED_HOSTS = ['*']
DEBUG = env.bool('DJANGO_DEBUG', default=True)
