import logging

from bs4 import BeautifulSoup

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.http.response import HttpResponseForbidden
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from crispy_forms.utils import render_crispy_form
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field
from crispy_forms.bootstrap import StrictButton

from core import components

logger = logging.getLogger("mardid")

class SimpleLookupForm(forms.ModelForm):

    def get_update_url(self):
        return self.update_url

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        url = self.get_update_url()
        submit_url = (reverse_lazy(url, args=[self.instance.pk])
                      if self.instance.pk else
                      reverse_lazy(url))
        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_area",
            'hx-post': submit_url
        }
        btn_submit = StrictButton('<span class="bi bi-check-square"></span>',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_submit_attrs)

        # Dynamically create columns for each field
        field_columns = []
        excluded_fields = ['id']  # Fields to exclude from the layout

        for field_name in self.fields:
            if field_name not in excluded_fields:
                field_columns.append(
                    Column(Field(field_name), css_class='form-control-sm')
                )

        self.helper.layout = Layout(
            Div(
                Div(
                    Row(*field_columns),
                    Row(
                        Column(btn_submit)
                    ),
                    css_class='card-body'
                ),
                css_class='card mb-2'
            )
        )


class SimpleLookupView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):

    template_name = 'core/view_lookup.html'
    login_url = reverse_lazy('login')
    table_url = None

    def test_func(self):
        return self.request.user.groups.filter(name='MarDID Maintainers').exists()

    def get_table_url(self):
        return self.table_url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_update_url'] = self.get_table_url()

        return context


def create_lookup_classes(lookup_model, name_key):
    """Factory function to create lookup form and view classes dynamically"""
    # Generate names
    name_update_lookup = f'update_lookup_{name_key}'
    name_list_lookup = f'list_{name_key}'

    # Create form class dynamically
    class DynamicLookupForm(SimpleLookupForm):
        update_url = f'core:{name_update_lookup}'

        class Meta:
            fields = "__all__"
            model = lookup_model

    # Create view class dynamically
    class DynamicLookupView(SimpleLookupView):
        table_url = reverse_lazy(f'core:{name_list_lookup}')

    # Set proper names for better debugging and introspection
    DynamicLookupForm.__name__ = f"{lookup_model.__name__}Form"
    DynamicLookupView.__name__ = f"{lookup_model.__name__}View"

    return DynamicLookupForm, DynamicLookupView


def prep_table(request, dataframe, form_url, delete_url):
    table_html = dataframe.to_html()
    df_soup = BeautifulSoup(f'{table_html}', 'html.parser')

    table = df_soup.find('table')
    table.attrs['class'] = 'table table-striped table-sm'
    table.attrs['hx-get'] = request.path
    table.attrs['hx-trigger'] = 'update_table from:body'
    table.attrs['hx-swap'] = 'outerHTML'
    table.attrs['id'] = 'table_id_cruise_list'

    table_head = table.find('thead')
    table_head.attrs['class'] = 'sticky-top bg-white'
    table_head.find('tr').find_next('tr').decompose()
    for th in table_head.find('tr').find_all('th'):
        th.attrs['class'] = 'text-start'

    table_body = table.find('tbody')
    for tr in table_body.find_all('tr'):
        th = tr.find('th')
        id = int(th.string)
        row_id = f'tr_id_lookup_{id}'
        tr.attrs['id'] = row_id
        th.string = ""
        th.append(btn_edit:=df_soup.new_tag('button'))
        th.append(btn_delete:=df_soup.new_tag('button'))

        btn_edit.append(span_edt:=df_soup.new_tag('span'))
        btn_edit.attrs['class'] = 'btn btn-sm btn-outline-dark'
        btn_edit.attrs['hx-get'] = reverse_lazy(form_url, args=[id])
        btn_edit.attrs['hx-target'] = "#form_area"
        btn_edit.attrs['hx-swap'] = "innerHTML"
        span_edt.attrs['class'] = 'bi bi-pencil-square'

        btn_delete.append(span_del:=df_soup.new_tag('span'))

        btn_delete.attrs['class'] = 'ms-2 btn btn-sm btn-danger'
        btn_delete.attrs['hx-target'] = f'#{row_id}'
        btn_delete.attrs['hx-confirm'] = _("Are you sure you want to delete this?")
        btn_delete.attrs['hx-post'] = reverse_lazy(delete_url, args=[id])
        span_del.attrs['class'] = 'bi bi-dash-square'

    form_row = table_head.find('tr')
    td = form_row.find('th')
    td.append(btn_add:=df_soup.new_tag('button'))
    btn_add.append(span_add:=df_soup.new_tag('span'))
    btn_add.attrs['class'] = "btn btn-sm btn-outline-dark"
    btn_add.attrs['hx-get'] = reverse_lazy(form_url)
    btn_add.attrs['hx-target'] = "#form_area"
    btn_add.attrs['hx-swap'] = "innerHTML"
    span_add.attrs['class'] = 'bi bi-plus-square'

    return df_soup


def get_lookup_form(model_form, **kwargs):
    if 'pk' in kwargs:
        location = model_form.Meta.model.objects.get(pk=kwargs['pk'])
        form = model_form(instance=location)
    else:
        form = model_form()

    return form


@login_required(login_url=reverse_lazy('login'))
def update_lookup(request, model_form, **kwargs):
    # Check if user belongs to MarDID Maintainer group
    if not request.user.groups.filter(name='MarDID Maintainers').exists():
        return HttpResponseForbidden(_("You must be a MarDID Maintainer to perform this action."))

    if 'pk' in kwargs:
        location = model_form.Meta.model.objects.get(pk=kwargs['pk'])
        form = model_form(request.POST, instance=location)
    else:
        form = model_form(request.POST)

    if form.is_valid():
        form.save()
        response = HttpResponse()
        response['HX-Trigger'] = 'update_table'
        return response

    response = HttpResponse(render_crispy_form(form))
    return response


@login_required(login_url=reverse_lazy('login'))
def delete_element(request, pk, lookup_model):
    # Check if user belongs to MarDID Maintainer group
    if not request.user.groups.filter(name='MarDID Maintainers').exists():
        return HttpResponseForbidden(_("You must be a MarDID Maintainer to perform this action."))

    try:
        element = lookup_model.objects.get(pk=pk)
        element.delete()
    except ValidationError as ex:
        message = _("This value is being used and cannot be deleted.")
        logger.error(message)

        soup = BeautifulSoup("", "html.parser")

        alert = components.get_alert(f'div_id_issue_{pk}', 'danger', message)
        alert.append(row:=soup.new_tag("div", attrs={"class": "row"}))
        row.append(col:=soup.new_tag("div", attrs={"class": "col"}))
        col.append(ul:=soup.new_tag("ul"))
        ul.append(li:=soup.new_tag("li"))

        li.string = str(element)

        soup.append(span:=soup.new_tag("span", attrs={"id": "span_id_alerts", "hx-swap-oob": "beforeend"}))
        span.append(alert)

        response = HttpResponse(soup)
        response['HX-Trigger'] = 'update_table'
        return response

    response = HttpResponse()
    response['HX-Trigger'] = 'update_table'
    return response
