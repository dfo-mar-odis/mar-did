import logging
import pandas as pd

from bs4 import BeautifulSoup

from django import forms
from django.contrib.auth.decorators import login_required
from django.db.models import Min
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.http import HttpResponse, HttpResponseForbidden
from django.views.generic.base import TemplateView
from django.template.loader import render_to_string

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field

from urllib.parse import urlencode, parse_qs

from core.utils import redirect_if_not_superuser
from core.views.forms import form_mission
from core import models

logger = logging.getLogger('mardid')

class MissionListView(TemplateView):
    template_name = 'core/view_mission_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mission List'
        context['container'] = 'container-fluid'
        context['filter_form'] = MissionFilter()
        return context


class MissionFilter(forms.Form):

    descriptor = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Mission Descriptor')
    )

    name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Mission Name')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        target = "#input_id_mission_submit"
        url = reverse_lazy('core:submit_mission_filter_form')

        select_attrs = {
            'hx-get': url,
            'hx-swap': 'outHTML',
            'hx-target': target
        }

        text_attrs = {
            'hx-get': url,
            'hx-swap': 'outerHTML',
            'hx-trigger': 'keydown delay:1s',
            'hx-target': target
        }

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(Field('name', css_class="form-control form-control-sm", **text_attrs), css_class="col-2"),
                Column(Field('descriptor', css_class="form-control form-control-sm", **text_attrs), css_class="col-2"),
            ),
        )


def list_missions(request):

    page = int(request.GET.get('page', 0) or 0)
    page_limit = 25
    page_start = page_limit * page
    page_end = page_start + page_limit

    # Example query to order missions by the start_date of their first leg
    queryset = models.Missions.objects.annotate(first_leg_start_date=Min('legs__number')).order_by('-first_leg_start_date')
    if name:=request.GET.get('name', None):
        queryset = queryset.filter(name__icontains=name)

    if descriptor:=request.GET.get('descriptor', None):
        queryset = queryset.filter(descriptor__icontains=descriptor)

    queryset = queryset[page_start:page_end]

    if not queryset:
        if page <= 0:
            html = render_to_string('core/partials/table_missions.html', request=request)
            return HttpResponse(html)
        else:
            return HttpResponse()

    context = {
        "missions": queryset
    }
    html = render_to_string('core/partials/table_missions.html', context, request=request)

    table_soup = BeautifulSoup(html, "html.parser")
    tbody = table_soup.find('tbody')
    tbody.attrs['id'] = 'tbody_id_mission_list'
    trs = tbody.findAll('tr', recursive=False)
    if len(trs) > 10:
        query_params = parse_qs(request.GET.urlencode())
        query_params['page'] = page + 1
        new_query_string = urlencode(query_params, doseq=True)

        # we can show up to 10 TRs on the screen, but not having the trigger on the very last
        # row we can start the loading process before the user gets to the final TR.
        last_tr = trs[-10]
        last_tr.attrs['hx-trigger'] = 'intersect once'
        last_tr.attrs['hx-get'] = request.path + f"?{new_query_string}"
        last_tr.attrs['hx-target'] = "#tbody_id_mission_list"
        last_tr.attrs['hx-swap'] = 'beforeend'

    if page > 0:
        return HttpResponse(trs)

    return HttpResponse(table_soup)


def delete_mission(request, mission_id):
    next_page = reverse_lazy('core:mission_view')
    if response:=redirect_if_not_superuser(request, next_page):
        return response

    mission = models.Missions.objects.get(pk=mission_id)
    mission.delete()

    response = HttpResponse()
    response['HX-Trigger'] = "update_mission_list"
    return response


def submit_filter_form(request):
    response = HttpResponse('<input id="input_id_mission_submit" type="hidden" name="submit" value="submit" />')
    response['HX-Trigger'] = "update_mission_list"
    return response


def clear_filter_form(request):
    context = {
        'filter_form': MissionFilter()
    }

    html = render_to_string("core/partials/form_filter_missions.html", context=context)
    response = HttpResponse(html)
    return response


urlpatterns = [
    path('mission', MissionListView.as_view(), name='mission_view'),
    path('mission/list', list_missions, name='list_missions'),
    path('mission/delete/<int:mission_id>', delete_mission, name='delete_mission'),
    path('mission/submit_fitler_form', submit_filter_form, name='submit_mission_filter_form'),
    path('mission/clear_fitler_form', clear_filter_form, name='clear_mission_filter_form')
]

urlpatterns += form_mission.urlpatterns
