from typing import Callable, Any, Type

from bs4 import BeautifulSoup
from crispy_forms.bootstrap import StrictButton, FieldWithButtons
from crispy_forms.layout import Field, Div, Row, HTML
from crispy_forms.utils import render_crispy_form
from django import forms
from django.db import models
from django.template.loader import render_to_string
from django.urls import reverse_lazy


class MultiselectContext:
    prefix: str
    lookup_model: Type[models.Model]
    form_class: Type[forms.ModelForm]
    render_function: Callable[[Any], str]
    add_url: str
    remove_url: str

    def __init__(self, prefix: str, lookup_model: Type[models.Model], form_class: Type[forms.ModelForm],
                 render_function: Callable[[Any], str], add_url: str, remove_url: str):
        self.prefix = prefix
        self.lookup_model = lookup_model
        self.form_class = form_class
        self.render_function = render_function
        self.add_url = add_url
        self.remove_url = remove_url


class MultiselectFieldForm(forms.ModelForm):

    def get_multiselect_context(self, prefix) -> MultiselectContext:
        raise NotImplementedError("You must implement the get_multiselect_context method to return a MultiselectContext instance.")

    def clean_multiselect_field(self, prefix, lookup_model):
        input_select = self.data.get(f'{prefix}_select')
        input_list = self.data.getlist(f'{prefix}_bullet')

        if not input_list and input_select:
            input_list = [input_select]

        keys = [int(location) for location in input_list]
        if input_select:
            keys.append(int(input_select))

        cleaned_elements = lookup_model.objects.filter(pk__in=keys)

        if not cleaned_elements.exists():
            return None

        return cleaned_elements

    def get_list_add_btn(self, prefix) -> StrictButton:

        btn_add_attrs = {
            'hx-target': f"#div_id_{prefix}",
            'hx-post': reverse_lazy(self.get_multiselect_context(prefix).add_url, args=[prefix]),
            'hx-swap': "beforeend"
        }

        btn_add = StrictButton('<span class="bi bi-plus-square"></span>',
                               css_class='btn btn-sm btn-primary',
                               **btn_add_attrs)

        return btn_add

    def get_list_container(self, prefix, _list):
        btn_add = self.get_list_add_btn(prefix)
        select_field = FieldWithButtons(
            Field(f'{prefix}_select', css_class='form-select-sm'),
            btn_add,
            css_class='input-group-sm'
        )
        component = Div(
            select_field,
            Row(
                Field(prefix, wrapper_class="d-none"),
                HTML(_list),
                id=f'div_id_{prefix}',
            ),
            css_class='card card-body border border-dark mb-2'
        )
        return component

    def init_lookup(self, prefix):
        _list = ""
        lookups = []

        multiselect_context = self.get_multiselect_context(prefix)
        model = multiselect_context.lookup_model
        if self.instance.pk:
            lookup_list = getattr(self.instance, prefix)
            lookups = [lu.id for lu in lookup_list.all()] if self.instance.pk else []

        if not lookups:
            if self.data and f'{prefix}_bullet' in self.data:
                lookups = self.data.getlist(f'{prefix}_bullet')

        for lu_id in lookups:
            _list += get_list_bullet(multiselect_context, lu_id)

        self.fields[f'{prefix}_select'].queryset = model.objects.all()
        self.fields[prefix].queryset = model.objects.all()

        return self.get_list_container(prefix, _list)

def get_list_bullet(multiselect_context: MultiselectContext, element_id: int):

    prefix = multiselect_context.prefix
    element = multiselect_context.lookup_model.objects.get(pk=element_id)

    context = {
        'input_name': f'{prefix}_bullet',
        'value_id': element.pk,
        'value_label': multiselect_context.render_function(element),
        'post_url': reverse_lazy(multiselect_context.remove_url, args=[prefix, element.pk]),
    }
    return render_to_string('core/partials/components/multi_select_bullet.html', context=context)


def remove_from_list(request, multiselect_context: MultiselectContext, element_id: int) -> BeautifulSoup | None:
    existing_ids = [int(id) for id in request.POST.getlist(multiselect_context.prefix)]
    if element_id not in existing_ids:
        return None

    soup = BeautifulSoup()

    existing_ids.remove(element_id)
    soup.append(get_updated_list(request, multiselect_context))

    return soup


def add_to_list(request, multiselect_context: MultiselectContext, prefix: str) -> BeautifulSoup | None:

    new_id = request.POST.get(f'{prefix}_select')
    existing = request.POST.getlist(f'{prefix}_bullet')

    # if an id already exists in the list we don't add it again.
    if new_id in existing:
        return None

    element_id: int = int(new_id)
    soup = BeautifulSoup()

    new_pill = get_list_bullet(multiselect_context, element_id)

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    existing_ids.append(element_id)

    soup.append(get_updated_list(request, multiselect_context))
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return soup


def get_updated_list(request, multiselect_context: MultiselectContext) -> BeautifulSoup:

    existing_ids = [int(id) for id in request.POST.getlist(multiselect_context.prefix)]
    form = multiselect_context.form_class(initial={multiselect_context.prefix: existing_ids})

    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    form_select = form_soup.find(id=f"id_{multiselect_context.prefix}")
    form_select.attrs['hx-swap'] = 'outerHTML'
    form_select.attrs['hx-swap-oob'] = 'true'

    return form_select
