import logging
import pandas as pd

from bs4 import BeautifulSoup

<<<<<<< HEAD
from django import forms
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.views.generic.base import TemplateView
from django.template.loader import render_to_string

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field

from urllib.parse import urlencode, parse_qs

from core.views.forms import form_cruise
=======
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django_pandas.io import read_frame
from django.views.generic.base import TemplateView
from django.template.loader import render_to_string

from core.forms import form_cruise
>>>>>>> 8aa4604 (added alerts and delete functions)
from core import models

logger = logging.getLogger('mardid')

class CruiseListView(TemplateView):
    template_name = 'core/view_cruise_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Cruise List'
        context['container'] = 'container-fluid'
<<<<<<< HEAD
        context['filter_form'] = CruiseFilter()
        return context


class CruiseFilter(forms.Form):

    descriptor = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Cruise Descriptor')
    )

    name = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label=_('Cruise Name')
    )

    program = forms.ModelChoiceField(
        queryset=models.Programs.objects.all(),
        empty_label=_("Select a program"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        target = "#input_id_cruise_submit"
        url = reverse_lazy('core:submit_cruise_filter_form')

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
                Column(Field('program', css_class="form-select form-select-sm", **select_attrs), css_class="col-2"),
            ),
        )


def list_cruises(request):

    page = int(request.GET.get('page', 0) or 0)
    page_limit = 25
    page_start = page_limit * page
    page_end = page_start + page_limit

    table_soup = BeautifulSoup('', 'html.parser')

    queryset = models.Cruises.objects.order_by('pk').prefetch_related('programs', 'chief_scientists', 'locations')
    if name:=request.GET.get('name', None):
        queryset = queryset.filter(name__icontains=name)

    if descriptor:=request.GET.get('descriptor', None):
        queryset = queryset.filter(descriptor__icontains=descriptor)

    if program:=request.GET.get('program', None):
        program_id = int(program)
        program = models.Programs.objects.get(pk=program_id)
        queryset = queryset.filter(programs=program)

    queryset = queryset[page_start:page_end]

    if not queryset:
        if page <= 0:
            html = render_to_string('core/partials/table_cruises.html', context={'user': request.user})
            return HttpResponse(html)
        else:
            return HttpResponse()

    context = {
        "cruises": queryset
    }
    html = render_to_string('core/partials/table_cruises.html', context)

    table_soup = BeautifulSoup(html, "html.parser")
    tbody = table_soup.find('tbody')
    tbody.attrs['id'] = 'tbody_id_cruise_list'
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
        last_tr.attrs['hx-target'] = "#tbody_id_cruise_list"
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
        data_btn.attrs['title'] = _('Cruise Data')
        span.attrs['class'] = "bi bi-bar-chart"

        if request.user.groups.filter(name__in=["Chief Scientists", "MarDID Maintainers"]):
            first_th.append(update_btn:=table_soup.new_tag('a'))
            update_btn.append(span := table_soup.new_tag("span"))
            update_btn.attrs['class'] = "btn btn-sm btn-dark ms-2"
            update_btn.attrs['href'] = reverse_lazy('core:update_cruise_view', args=[int(id)])
            update_btn.attrs['title'] = _('Update cruise')
            span.attrs['class'] = "bi bi-pencil-square"

            if request.user.groups.filter(name__iexact="MarDID Maintainers").exists():
                row_id = f"tr_id_cruise_{id}"
                tr.attrs['id'] = row_id
                first_th.append(del_btn := table_soup.new_tag('a'))
                del_btn.append(span := table_soup.new_tag("span"))
                del_btn.attrs['class'] = "btn btn-sm btn-danger ms-2"
                del_btn.attrs['title'] = _('Delete cruise')
                del_btn.attrs['hx-confirm'] = _("Are you sure you want to delete this curise?")
                del_btn.attrs['hx-post'] = reverse_lazy('core:delete_cruise', args=[int(id)])
                del_btn.attrs['hx-target'] = f"#{row_id}"
                del_btn.attrs['hx-swap'] = "delete"
                span.attrs['class'] = "bi bi-x-square"

    if page > 0:
        return HttpResponse(trs)

    table = table_soup.find("table")
    table.attrs['class'] = 'table table-striped table-sm'
    # table.attrs['hx-get'] = request.path
    # table.attrs['hx-trigger'] = 'update_cruise_list from:body'
    # table.attrs['hx-swap'] = 'outerHTML'
=======
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
            if request.user.is_authenticated:
                id = int(first_th.string)
                first_th.string = ""
                first_th.append(update_btn:=df_soup.new_tag('a'))
                update_btn.append(span := df_soup.new_tag("span"))
                update_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
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

            else:
                first_th.decompose()

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
>>>>>>> 8aa4604 (added alerts and delete functions)
    table.attrs['id'] = 'table_id_cruise_list'

    t_head = table.find('thead')
    t_head.attrs['class'] = 'sticky-top bg-white'

<<<<<<< HEAD
    th = t_head.find('th')
    if request.user.is_authenticated:
        th.append(add_btn:=table_soup.new_tag("a"))
        add_btn.attrs['class'] = "btn btn-sm btn-outline-dark"
        add_btn.attrs['href'] = reverse_lazy('core:new_cruise_view')
        add_btn.attrs['title'] = _('Add a new cruise')
        add_btn.append(span:= table_soup.new_tag("span"))
        span.attrs['class'] = "bi bi-plus-square"
=======
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
    else:
        th.decompose()
>>>>>>> 8aa4604 (added alerts and delete functions)

    for th in t_head.find_all('th'):
        th.attrs['class'] = 'text-start'

<<<<<<< HEAD
    return HttpResponse(table_soup)


def authenticated(request):
    # Check if user belongs to MarDID Maintainers or Chief Scientists groups
    if request.user.groups.filter(name__in=['MarDID Maintainers']).exists():
        return True

    return False


def delete_cruise(request, cruise_id):
    if not authenticated(request):
        next_page = reverse_lazy('core:data_view', args=[cruise_id])
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return response

    cruise = models.Cruises.objects.get(pk=cruise_id)
=======
    return HttpResponse(df_soup)


def delete_cruise(request, pk):

    cruise = models.Cruises.objects.get(pk=pk)
>>>>>>> 8aa4604 (added alerts and delete functions)
    cruise.delete()

    response = HttpResponse()
    response['HX-Trigger'] = "update_cruise_list"
    return response


<<<<<<< HEAD
def submit_filter_form(request):
    response = HttpResponse('<input id="input_id_cruise_submit" type="hidden" name="submit" value="submit" />')
    response['HX-Trigger'] = "update_cruise_list"
    return response


def clear_filter_form(request):
    context = {
        'filter_form': CruiseFilter()
    }

    html = render_to_string("core/partials/form_filter_cruises.html", context=context)
    response = HttpResponse(html)
    return response


urlpatterns = [
    path('cruise', CruiseListView.as_view(), name='cruise_view'),
    path('cruise/list', list_cruises, name='list_cruises'),
    path('cruise/delete/<int:cruise_id>', delete_cruise, name='delete_cruise'),
    path('cruise/submit_fitler_form', submit_filter_form, name='submit_cruise_filter_form'),
    path('cruise/clear_fitler_form', clear_filter_form, name='clear_cruise_filter_form')
=======
urlpatterns = [
    path('', CruiseListView.as_view(), name='cruise_view'),
    path('cruise/list', list_cruises, name='list_cruises'),
    path('cruise/delete/<int:pk>', delete_cruise, name='delete_cruise')
>>>>>>> 8aa4604 (added alerts and delete functions)
]

urlpatterns += form_cruise.urlpatterns