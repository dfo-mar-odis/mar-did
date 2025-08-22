import logging
import pandas as pd

from bs4 import BeautifulSoup

from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.template.loader import render_to_string

from core.views.forms import form_cruise
from core import models

logger = logging.getLogger('mardid')

class CruiseListView(TemplateView):
    template_name = 'core/view_cruise_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cruise List'
        context['container'] = 'container-fluid'
        return context


def list_cruises(request):
    page = int(request.GET.get('page', 0) or 0)
    page_limit = 100
    page_start = page_limit * page

    table_soup = BeautifulSoup('', 'html.parser')

    headers = [
        ('name', _("Name")),
        ('descriptor', _("Descriptor")),
        ('start_date', _("Start Date")),
        ('end_date', _("End Date")),
        ('chief_scientists', _("Chief Scientists")),
        ('locations', _("Geographic Regions"))
    ]

    value_headers = ['id'] + [h[0] for h in headers]
    table_headers = [h[1] for h in headers]

    queryset = models.Cruises.objects.prefetch_related('chief_scientists', 'locations')
    queryset_list = []
    for cruise in queryset:
        queryset_list.append({
            'id': cruise.id,
            'name': cruise.name,
            'descriptor': cruise.descriptor,
            'start_date': cruise.start_date,
            'end_date': cruise.end_date,
            'chief_scientists': ', '.join(f'{scientist.last_name}, {scientist.first_name}' for scientist in cruise.chief_scientists.all().order_by('last_name', 'first_name')),
            'locations': ', '.join(str(location) for location in cruise.locations.all()),
        })

    if queryset_list:
        df = pd.DataFrame(queryset_list)
        df.set_index('id', inplace=True)
        df.columns = table_headers

        # Pandas has the ability to render dataframes as HTML and it's super fast, but the default table looks awful.
        # Use BeautifulSoup for html manipulation to post process the HTML table Pandas created
        table_html = df.to_html()
        df_soup = BeautifulSoup(f'{table_html}', 'html.parser')

        trs = df_soup.find('tbody').findAll('tr', recursive=False)
        for tr in trs:
            first_th = tr.find('th')
            id = int(first_th.string)
            first_th.string = ""
            first_th.append(data_btn := df_soup.new_tag('a'))
            data_btn.append(span := df_soup.new_tag("span"))
            data_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
            data_btn.attrs['href'] = reverse_lazy('core:data_view', args=[int(id)])
            data_btn.attrs['title'] = _('Cruise Data')
            span.attrs['class'] = "bi bi-bar-chart"

            if request.user.is_authenticated:
                first_th.append(update_btn:=df_soup.new_tag('a'))
                update_btn.append(span := df_soup.new_tag("span"))
                update_btn.attrs['class'] = "btn btn-sm btn-dark ms-2"
                update_btn.attrs['href'] = reverse_lazy('core:update_cruise_view', args=[int(id)])
                update_btn.attrs['title'] = _('Update cruise')
                span.attrs['class'] = "bi bi-pencil-square"

                if request.user.groups.filter(name__iexact="MarDID Maintainer").exists():
                    row_id = f"tr_id_cruise_{id}"
                    tr.attrs['id'] = row_id
                    first_th.append(del_btn := df_soup.new_tag('a'))
                    del_btn.append(span := df_soup.new_tag("span"))
                    del_btn.attrs['class'] = "btn btn-sm btn-danger ms-2"
                    del_btn.attrs['title'] = _('Delete cruise')
                    del_btn.attrs['hx-confirm'] = _("Are you sure you want to delete this curise?")
                    del_btn.attrs['hx-post'] = reverse_lazy('core:delete_cruise', args=[int(id)])
                    del_btn.attrs['hx-target'] = f"#{row_id}"
                    del_btn.attrs['hx-swap'] = "delete"
                    span.attrs['class'] = "bi bi-x-square"

        if page > 0:
            return HttpResponse(trs)
    else:
        table_html = render_to_string('core/partial/table_cruise.html')
        df_soup = BeautifulSoup(table_html, 'html.parser')

    table = df_soup.find("table")
    table.attrs['class'] = 'table table-striped table-sm'
    table.attrs['hx-get'] = request.path
    table.attrs['hx-trigger'] = 'update_cruise_list from:body'
    table.attrs['hx-swap'] = 'outerHTML'
    table.attrs['id'] = 'table_id_cruise_list'

    t_head = table.find('thead')
    t_head.attrs['class'] = 'sticky-top bg-white'

    if (tr:=t_head.find('tr')) and (tr:=tr.find_next('tr')):
        # remove the second table row from the t-head
        t_head.find('tr').find_next("tr").decompose()

    th = t_head.find('th')
    if request.user.is_authenticated:
        th.append(add_btn:=df_soup.new_tag("a"))
        add_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
        add_btn.attrs['href'] = reverse_lazy('core:new_cruise_view')
        add_btn.attrs['title'] = _('Add a new cruise')
        add_btn.append(span:= df_soup.new_tag("span"))
        span.attrs['class'] = "bi bi-plus-square"

    for th in t_head.find_all('th'):
        th.attrs['class'] = 'text-start'

    return HttpResponse(df_soup)


def delete_cruise(request, pk):

    cruise = models.Cruises.objects.get(pk=pk)
    cruise.delete()

    response = HttpResponse()
    response['HX-Trigger'] = "update_cruise_list"
    return response


urlpatterns = [
    path('cruise', CruiseListView.as_view(), name='cruise_view'),
    path('cruise/list', list_cruises, name='list_cruises'),
    path('cruise/delete/<int:pk>', delete_cruise, name='delete_cruise')
]

urlpatterns += form_cruise.urlpatterns