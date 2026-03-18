import logging
import pandas as pd

from bs4 import BeautifulSoup

from django import forms
from django.contrib.auth.decorators import login_required
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

    table_soup = BeautifulSoup('', 'html.parser')

    queryset = models.Missions.objects.order_by('pk')
    if name:=request.GET.get('name', None):
        queryset = queryset.filter(name__icontains=name)

    if descriptor:=request.GET.get('descriptor', None):
        queryset = queryset.filter(descriptor__icontains=descriptor)

    queryset = queryset[page_start:page_end]

    if not queryset:
        if page <= 0:
            html = render_to_string('core/partials/table_missions.html', context={'user': request.user})
            return HttpResponse(html)
        else:
            return HttpResponse()

    context = {
        "missions": queryset
    }
    html = render_to_string('core/partials/table_missions.html', context)

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

    for tr in trs:
        first_th = tr.find('th')
        first_th.attrs['style'] = "width: 2%; white-space: nowrap;"
        id = int(first_th.string)
        first_th.string = ""
        first_th.append(data_btn := table_soup.new_tag('a'))
        data_btn.append(span := table_soup.new_tag("span"))
        data_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
        data_btn.attrs['href'] = reverse_lazy('core:data_view', args=[int(id)])
        data_btn.attrs['title'] = _('mission Data')
        span.attrs['class'] = "bi bi-bar-chart"

        if request.user.groups.filter(name__in=["Chief Scientists", "MarDID Maintainers"]):
            first_th.append(update_btn:=table_soup.new_tag('a'))
            update_btn.append(span := table_soup.new_tag("span"))
            update_btn.attrs['class'] = "btn btn-sm btn-dark ms-2"
            update_btn.attrs['href'] = reverse_lazy('core:update_mission_view', args=[int(id)])
            update_btn.attrs['title'] = _('Update mission')
            span.attrs['class'] = "bi bi-pencil-square"

            if request.user.is_superuser:
                row_id = f"tr_id_mission_{id}"
                tr.attrs['id'] = row_id
                first_th.append(del_btn := table_soup.new_tag('a'))
                del_btn.append(span := table_soup.new_tag("span"))
                del_btn.attrs['class'] = "btn btn-sm btn-danger ms-2"
                del_btn.attrs['title'] = _('Delete mission')
                del_btn.attrs['hx-confirm'] = _("Are you sure you want to delete this curise?")
                del_btn.attrs['hx-post'] = reverse_lazy('core:delete_mission', args=[int(id)])
                del_btn.attrs['hx-target'] = f"#{row_id}"
                del_btn.attrs['hx-swap'] = "delete"
                span.attrs['class'] = "bi bi-x-square"

    if page > 0:
        return HttpResponse(trs)

    table = table_soup.find("table")
    table.attrs['class'] = 'table table-striped table-sm'
    # table.attrs['hx-get'] = request.path
    # table.attrs['hx-trigger'] = 'update_mission_list from:body'
    # table.attrs['hx-swap'] = 'outerHTML'
    table.attrs['id'] = 'table_id_mission_list'

    t_head = table.find('thead')
    t_head.attrs['class'] = 'sticky-top bg-white'
    th = t_head.find('th')
    if request.user.is_authenticated:
        th.append(add_btn:=table_soup.new_tag("a"))
        add_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
        add_btn.attrs['href'] = reverse_lazy('core:new_mission_view')
        add_btn.attrs['title'] = _('Add a new mission')
        add_btn.append(span:= table_soup.new_tag("span"))
        span.attrs['class'] = "bi bi-plus-square"

    for th in t_head.find_all('th'):
        th.attrs['class'] = 'text-start'

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
