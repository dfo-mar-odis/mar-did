from django.urls import path
from . import view_cruises

app_name = 'core'

urlpatterns = []

urlpatterns += view_cruises.urlpatterns