from django.urls import path
from django.http import HttpResponse
from django_pandas.io import read_frame
from django.utils.translation import gettext as _

from crispy_forms.utils import render_crispy_form

from core import models
from core.views import view_lookup_abstract

# If copy and pasting this module as a template, change the lookup model to match
# the model of the simple look up class being extended
lookup_model = models.GeographicRegions

# These are the url aliases. If copy and pasting this module as a template, just change the
# name key for the simple lookup table.
name_key = 'geo_regions'
<<<<<<< HEAD
columns = ['name', 'description']
=======
>>>>>>> 8aa4604 (added alerts and delete functions)

###### DO NOT CHANGE THESE #############
name_get_form = f'lookup_form_{name_key}'
name_list_lookup = f'list_{name_key}'
name_get_view = f'lookup_view_{name_key}'
name_update_lookup = f'update_lookup_{name_key}'
name_delete_element = f'lookup_delete_{name_key}'

model_form, model_view = view_lookup_abstract.create_lookup_classes(lookup_model, name_key)
<<<<<<< HEAD

field_lookup = {field.name: field for field in lookup_model._meta.fields if field.name in columns}
labels = [(field_lookup[col_name].verbose_name if field_lookup[col_name].verbose_name else col_name) for col_name in columns]
=======
>>>>>>> 8aa4604 (added alerts and delete functions)
########################################

# The list function may have to be updated if the model doesn't fit the standard
# id, name, description format most simple lookup tables follow.
def list_lookup(request):

    queryset = lookup_model.objects.all().order_by('name')
<<<<<<< HEAD
    queryset_list = queryset.values_list('id', *columns)

    df = read_frame(queryset_list)
    df.set_index('id', inplace=True)
    df.columns = labels
=======
    queryset_list = queryset.values_list('id', 'name', 'description')

    df = read_frame(queryset_list)
    df.set_index('id', inplace=True)
    df.columns = [_("Name"), _("Description")]
>>>>>>> 8aa4604 (added alerts and delete functions)

    form_url_alias = f"core:{name_get_form}"
    delete_url_alias = f"core:{name_delete_element}"
    table = view_lookup_abstract.prep_table(request, df, form_url_alias, delete_url_alias)
    return HttpResponse(table)


def get_form(request, **kwargs):
    form = view_lookup_abstract.get_lookup_form(model_form, **kwargs)
    return HttpResponse(render_crispy_form(form))


def update_lookup(request, **kwargs):
    return view_lookup_abstract.update_lookup(request, model_form, **kwargs)


def delete_element(request, pk):
    return view_lookup_abstract.delete_element(request, pk, lookup_model)


urlpatterns = [
    path(f'lookup/{name_key}', model_view.as_view(), name=name_get_view),
    path(f'lookup/{name_key}/form', get_form, name=name_get_form),
    path(f'lookup/{name_key}/form/<int:pk>', get_form, name=name_get_form),
    path(f'lookup/{name_key}/table/list', list_lookup, name=name_list_lookup),
    path(f'lookup/{name_key}/add', update_lookup, name=name_update_lookup),
    path(f'lookup/{name_key}/update/<int:pk>', update_lookup, name=name_update_lookup),
    path(f'lookup/{name_key}/delete/<int:pk>', delete_element, name=name_delete_element)
]