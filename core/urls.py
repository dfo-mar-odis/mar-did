from django.urls import path
from django.conf import settings
from importlib import import_module
import os
import pkgutil

app_name = 'core'
urlpatterns = []

# Get the path to the views package
views_pkg = 'core.views'

# Iterate through all modules in the views package
for _, module_name, is_pkg in pkgutil.iter_modules([os.path.join('core', 'views')]):
    if not is_pkg:  # Skip if it's a package rather than a module
        try:
            # Import the module dynamically
            module = import_module(f'{views_pkg}.{module_name}')

            # Check if the module has urlpatterns
            if hasattr(module, 'urlpatterns'):
                urlpatterns += module.urlpatterns
                print(f"Added urlpatterns from {module_name}")
        except (ImportError, AttributeError) as e:
            print(f"Could not import urlpatterns from {module_name}: {e}")