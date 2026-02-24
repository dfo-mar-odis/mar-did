from django.urls import path
from django.http import HttpResponse
from django_pandas.io import read_frame
from django.utils.translation import gettext as _

from crispy_forms.utils import render_crispy_form

from mardid import models
from core.views import view_lookup_abstract

# If copy and pasting this module as a template, change the lookup model to match
# the model of the simple look up class being extended
lookup_model = models.EquipmentType

# These are the url aliases. If copy and pasting this module as a template, just change the
# name key for the simple lookup table.
app_name = 'mardid'
lookup_title = _('Equipment Types')
name_key = 'equipment_type'
columns = ['type', 'description']

###### DO NOT CHANGE THESE #############
model_form, model_view = view_lookup_abstract.create_lookup_classes(lookup_model, name_key, app_name, lookup_title)

field_lookup = {field.name: field for field in lookup_model._meta.fields if field.name in columns}
labels = [(field_lookup[col_name].verbose_name if field_lookup[col_name].verbose_name else col_name) for col_name in columns]
########################################

# The list function may have to be updated if the model doesn't fit the standard
# id, name, description format most simple lookup tables follow.
def list_lookup(request):

    queryset = lookup_model.objects.all().order_by('type')
    queryset_list = queryset.values_list('id', *columns)

    df = read_frame(queryset_list)
    df.set_index('id', inplace=True)
    df.columns = labels

    table = view_lookup_abstract.prep_table(request, df, app_name, name_key)
    return HttpResponse(table)


def get_form(request, **kwargs):
    form = view_lookup_abstract.get_lookup_form(model_form, **kwargs)
    return HttpResponse(render_crispy_form(form))


attrs = {
    'name_key': name_key,
    'lookup_model': lookup_model,
    'model_form': model_form,
    'model_view': model_view,
    'get_form': get_form,
    'list_lookup': list_lookup,
}


urlpatterns = view_lookup_abstract.get_url_patterns(**attrs)