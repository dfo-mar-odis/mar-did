from django.urls import path
from django.conf import settings
from importlib import import_module
import os
import pkgutil

app_name = 'core'
urlpatterns = []

# Get the path to the views package
views_pkg = 'core.views'

<<<<<<< HEAD
# I prefer to include url patterns with the views and forms they're expected to control
# this dynamically loads the url patterns form things in the 'views' package
=======
>>>>>>> 8aa4604 (added alerts and delete functions)
# Iterate through all modules in the views package
for _, module_name, is_pkg in pkgutil.iter_modules([os.path.join('core', 'views')]):
    if not is_pkg:  # Skip if it's a package rather than a module
        try:
            # Import the module dynamically
            module = import_module(f'{views_pkg}.{module_name}')

            # Check if the module has urlpatterns
            if hasattr(module, 'urlpatterns'):
                urlpatterns += module.urlpatterns
<<<<<<< HEAD
=======
                print(f"Added urlpatterns from {module_name}")
>>>>>>> 8aa4604 (added alerts and delete functions)
        except (ImportError, AttributeError) as e:
            print(f"Could not import urlpatterns from {module_name}: {e}")