from bs4 import BeautifulSoup

from django import forms
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.http.response import HttpResponseForbidden
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


class ExpectedDataForm(forms.ModelForm):
    class Meta:
        fields = ["cruise", "data_type", "status"]
        model = models.Dataset

    def __init__(self, *args, cruise, **kwargs):
        super().__init__(*args, **kwargs)

        status = models.DataStatus.objects.get(name__iexact='Expected')
        self.fields['cruise'].initial = cruise
        self.fields['status'].initial = status

        self.fields['cruise'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()

        submit_url = reverse_lazy('core:update_expected_data', args=[cruise.pk])
        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_area",
            'hx-post': submit_url
        }

        btn_submit = StrictButton('<span class="bi bi-check-square"></span>',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_submit_attrs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Div(
                    Field('cruise'),
                    Field('status'),
                    Row(
                        Column(
                            Field('data_type')
                        )
                    ),
                    btn_submit,
                    css_class="card-body"
                ),
                css_class="card mb-2"
            )
        )


class DataListView(TemplateView):
    template_name = "core/view_data_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Data List'
        context['object'] = models.Cruises.objects.get(pk=self.kwargs['pk'])
        context['container'] = 'container-fluid'
        return context


def list_data(request, cruise_id):
    cruise = models.Cruises.objects.get(pk=cruise_id)
    html = render_to_string('core/view_data_list.html', context={'object': cruise})
    soup = BeautifulSoup(html, 'html.parser')
    return HttpResponse(soup.find('table'))

def get_data_form(request, cruise_id):
    # Check if user belongs to MarDID Maintainer group
    if not request.user.groups.filter(name__in=['Chief Scientist', 'MarDID Maintainer']).exists():
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
    # Check if user belongs to MarDID Maintainer group
    if not request.user.groups.filter(name__in=['Chief Scientist', 'MarDID Maintainer']).exists():
        next_page = reverse_lazy('core:data_view', args=[cruise_id])
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return response

    cruise = models.Cruises.objects.get(pk=cruise_id)

    form = ExpectedDataForm(request.POST, cruise=cruise)
    if form.is_valid():
        form.save()
        response = HttpResponse()
        response['HX-Trigger'] = 'update_list'
        return response

    html = render_crispy_form(form)
    return HttpResponse(html)


urlpatterns = [
  path('data/<int:pk>', DataListView.as_view(), name='data_view'),
  path('data/<int:cruise_id>/list', list_data, name='list_data'),
  path('data/<int:cruise_id>/update_list', update_cruise_data, name='update_expected_data'),
  path('data/<int:cruise_id>/add_expected', get_data_form, name='get_expected_data_form')
] + form_data_submission.urlpatterns
