from bs4 import BeautifulSoup

from django import forms
from django.db.models import Q
from django.shortcuts import redirect
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView
from django.utils.translation import gettext as _

from crispy_forms.utils import render_crispy_form
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field
from crispy_forms.bootstrap import StrictButton

from core import models
from core.views.forms import form_data_submission


class DataListView(TemplateView):
    template_name = "core/view_data_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Data List'
        context['object'] = models.Cruises.objects.get(pk=self.kwargs['pk'])
        context['container'] = 'container-fluid'
        return context


class ExpectedDataForm(forms.ModelForm):

    data_type_filter = forms.CharField(label=_("Filter Data Types"), required=False)

    class Meta:
        fields = ["cruise", "data_type", "status"]
        model = models.Dataset

    def __init__(self, *args, cruise, **kwargs):
        filter = None
        if 'data_type_filter' in kwargs:
            filter = kwargs.pop('data_type_filter')

        super().__init__(*args, **kwargs)

        if filter:
            query = Q(name__icontains=filter) | Q(description__icontains=filter)
            self.fields['data_type'].choices = [(obj.pk, f"{obj}") for obj in models.DataTypes.objects.filter(query)]

        status = models.DataStatus.objects.get(name__iexact='Expected')
        self.fields['cruise'].initial = cruise
        self.fields['status'].initial = status

        self.fields['cruise'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()

        btn_submit = None
        if cruise:
            submit_url = reverse_lazy('core:update_expected_data', args=[cruise.pk])
            btn_submit_attrs = {
                'title': _("Submit"),
                'hx-target': "#form_cruise_data_form_area",
                'hx-post': submit_url
            }

            btn_submit = StrictButton(f'<span class="bi bi-plus-square"> {_("Add")}</span>',
                                      css_class='btn btn-sm btn-primary mb-1',
                                      **btn_submit_attrs)

        data_type_filter_attrs = {
            'hx-get': reverse_lazy('core:filter_data_types'),
            'hx-target': '#div_id_data_type',
            'hx-swap': 'innerHTML',
            'hx-trigger': 'keyup delay:1s'
        }
        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    Field('cruise'),
                    Field('status'),
                    Row(
                        Column(
                            Field('data_type_filter', **data_type_filter_attrs, css_class='form-control form-control-sm'),
                            css_class='col-2',
                        ),
                        Column(
                            Field('data_type', css_class='form-select form-select-sm'),
                            css_class='col'
                        )
                    ),
                    btn_submit if btn_submit else None,
                    css_class="card-body"
                ),
                css_class="card mb-2"
            )
        )


def list_data(request, cruise_id):
    cruise = models.Cruises.objects.get(pk=cruise_id)
    html = render_to_string('core/view_data_list.html', context={'object': cruise, 'user': request.user})
    soup = BeautifulSoup(html, 'html.parser')
    return HttpResponse(soup.find('table'))


def authenticated(request):
    # Check if user belongs to MarDID Maintainers or Chief Scientists groups
    if request.user.groups.filter(name__in=['Chief Scientists', 'Data Technicians', 'MarDID Maintainers']).exists():
        return True

    return False


def get_data_form(request, cruise_id):
    if not authenticated(request):
        next_page = reverse_lazy('core:data_view', args=[cruise_id])
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return response

    cruise = models.Cruises.objects.get(pk=cruise_id)
    form = ExpectedDataForm(cruise=cruise)
    html = render_crispy_form(form)

    return HttpResponse(html)


def update_cruise_data(request, cruise_id):
    if not authenticated(request):
        next_page = request.path
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return HttpResponse(response)

    cruise = models.Cruises.objects.get(pk=cruise_id)

    form = ExpectedDataForm(request.POST, cruise=cruise)
    if form.is_valid():
        form.save()
        response = HttpResponse(render_crispy_form(form))
        response['HX-Trigger'] = 'update_list'
        return response

    html = render_crispy_form(form)
    return HttpResponse(html)


def remove_expected(request, data_id):
    if not authenticated(request):
        next_page = request.path
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return HttpResponse(response)

    data = models.Dataset.objects.get(pk=data_id)
    data.delete()

    return HttpResponse()


def filter_data_types(request):
    filter = request.GET.get('data_type_filter', None)

    form = ExpectedDataForm(cruise=None, data_type_filter=filter)
    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')

    return HttpResponse(soup.find(id='div_id_data_type'))


urlpatterns = [
  path('data/<int:pk>', DataListView.as_view(), name='data_view'),
  path('data/<int:cruise_id>/list', list_data, name='list_data'),
  path('data/<int:cruise_id>/update_list', update_cruise_data, name='update_expected_data'),
  path('data/<int:cruise_id>/add_expected', get_data_form, name='get_expected_data_form'),
  path('data/remove/<int:data_id>', remove_expected, name='remove_data'),
  path('data/filter_data_types', filter_data_types, name='filter_data_types')
] + form_data_submission.urlpatterns
