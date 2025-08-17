from django.urls import path
from . import view_cruises, view_lookups

app_name = 'core'

urlpatterns = []

urlpatterns += view_cruises.urlpatterns
urlpatterns += view_lookups.urlpatterns