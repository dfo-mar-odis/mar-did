import pandas as pd
from bs4 import BeautifulSoup

from django.urls import path, reverse_lazy
from django.http import HttpResponse
from django_pandas.io import read_frame
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin

from . import models

class ContactRoleView(LoginRequiredMixin, TemplateView):
    template_name = 'core/view_lookup.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_update_url'] = reverse_lazy('core:contact_role_table_list')

        return context


class ContactView(LoginRequiredMixin, TemplateView):
    template_name = 'core/view_lookup.html'
    login_url = reverse_lazy('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['table_update_url'] = reverse_lazy('core:contact_table_list')

        return context


def prep_table(request, dataframe, model):
    table_html = dataframe.to_html()
    df_soup = BeautifulSoup(f'{table_html}', 'html.parser')

    table = df_soup.find('table')
    table.attrs['class'] = 'table table-striped table-sm'
    table.attrs['hx-get'] = request.path
    table.attrs['hx-trigger'] = 'update_table from:body'
    table.attrs['hx-swap'] = 'outerHTML'
    table.attrs['id'] = 'table_id_cruise_list'

    table_head = table.find('thead')
    table_head.find('tr').find_next('tr').decompose()
    for th in table_head.find('tr').find_all('th'):
        th.attrs['class'] = 'text-start'

    table_body = table.find('tbody')
    for tr in table_body.find_all('tr'):
        th = tr.find('th')
        id = int(th.string)
        th.string = ""
        th.append(btn_edit:=df_soup.new_tag('button'))
        th.append(btn_delete:=df_soup.new_tag('button'))

        btn_edit.append(span_edt:=df_soup.new_tag('span'))
        btn_edit.attrs['class'] = 'btn btn-sm btn-outline-dark'
        span_edt.attrs['class'] = 'bi bi-pencil-square'

        btn_delete.append(span_del:=df_soup.new_tag('span'))
        btn_delete.attrs['class'] = 'ms-2 btn btn-sm btn-danger'
        span_del.attrs['class'] = 'bi bi-dash-square'

    table_body.insert(0, form_row:=df_soup.new_tag('tr'))
    form_row.append(td := df_soup.new_tag('td'))
    td.append(btn_add:=df_soup.new_tag('button'))
    btn_add.append(span_add:=df_soup.new_tag('span'))
    btn_add.attrs['class'] = "btn btn-sm btn-outline-dark"
    span_add.attrs['class'] = 'bi bi-plus-square'

    for i in range(0, (dataframe.shape[1] )):
        form_row.append(td:=df_soup.new_tag('td'))
        column = dataframe.columns[i].lower().replace(' ', '_')

    return df_soup


def list_contact_roles(request):

    queryset = models.ContactRoles.objects.all()
    queryset_list = queryset.values_list('id', 'name', 'description')

    df = read_frame(queryset_list)
    df.set_index('id', inplace=True)
    df.columns = [_("Name"), _("Description")]

    df_soup = prep_table(request, df, models.ContactRoles)
    return HttpResponse(df_soup)


def list_contacts(request):

    queryset = models.Contacts.objects.all()
    queryset_list = []
    for contact in queryset:
        queryset_list.append({
            'id': contact.id,
            'last_name': contact.last_name,
            'first_name': contact.first_name,
            'roles': ", ".join([str(role) for role in contact.roles.all()])
        })

    df = pd.DataFrame(queryset_list)
    df.set_index('id', inplace=True)
    df.columns = [_("Last Name"), _("First Name"), _("Roles")]

    df_soup = prep_table(request, df, models.Contacts)
    return HttpResponse(df_soup)


urlpatterns = [
    path('lookup/contact', ContactView.as_view(), name='contact_view'),
    path('lookup/contact-role', ContactRoleView.as_view(), name='contact_role_view'),

    path('lookup/contact/table/list', list_contacts, name="contact_table_list"),
    path('lookup/contact-role/table/list', list_contact_roles, name="contact_role_table_list")
]