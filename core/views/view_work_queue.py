from http.client import responses
from urllib.parse import urlencode, parse_qs, urlsplit, urlunsplit
from bs4 import BeautifulSoup

from django import forms
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.utils.translation import gettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.urls import path, reverse_lazy
from django.views.generic import TemplateView

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field
from crispy_forms.bootstrap import StrictButton

from core import models

class WorkQueueFilter(forms.Form):

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

    status = forms.ModelChoiceField(
        queryset=models.DataStatus.objects.all(),
        empty_label=_("Select a status"),
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        url = reverse_lazy('core:list_work')
        target = '#table_id_workqueue_list'

        select_attrs = {
            'hx-get': url,
            'hx-swap': 'none'
        }

        text_attrs = {
            'hx-get': url,
            'hx-swap': 'none',
            'hx-trigger': 'keydown delay:1s'
        }

        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column(Field('name', css_class="form-control form-control-sm", **text_attrs), css_class="col-2"),
                Column(Field('descriptor', css_class="form-control form-control-sm", **text_attrs), css_class="col-2"),
                Column(Field('status', css_class="form-select form-select-sm", **select_attrs), css_class="col-2"),
            ),
        )

class WorkQueueView(TemplateView):
    template_name = 'core/view_work_queue.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        group = Group.objects.get(name__iexact="Datashop Processors")
        context['title'] = "Datashop Work Queue"
        context['filter_form'] = WorkQueueFilter()

        # context['datasets'] = models.Dataset.objects.all().order_by('-cruise__start_date')
        context['processors'] = User.objects.filter(groups=group)
        return context


def list_work(request):
    datasets = models.Dataset.objects.all().order_by('pk')

    if request.method == 'GET' and 'submit' not in request.GET:
        response = HttpResponse()
        response['HX-Trigger'] = 'update_list'
        return response

    if name:=request.GET.get('name', None):
        datasets = datasets.filter(cruise__name__icontains=name)

    if ident:=request.GET.get('descriptor', None):
        datasets = datasets.filter(cruise__descriptor__icontains=ident)

    if status_id:=request.GET.get('status', None):
        status = models.DataStatus(pk=status_id)
        datasets = datasets.filter(status=status)

    limit = 25
    page = int(request.GET.get('page', 0))
    start = page * limit
    end = (page+1) * limit
    datasets = datasets[start:end]

    group = Group.objects.get(name__iexact="Datashop Processors")
    context = {
        'user': request.user,
        'datasets': datasets,
        'processors': User.objects.filter(groups=group),
        'csrf_token': get_token(request)
    }
    html = render_to_string('core/partial/table_work_queue.html', context=context)
    soup = BeautifulSoup(html, 'html.parser')
    table = soup.find(id="table_id_workqueue_list")
    trs = table.find('tbody').find_all('tr')
    if len(trs) > 10:
        query_params = parse_qs(request.GET.urlencode())
        query_params['page'] = page+1
        new_query_string = urlencode(query_params, doseq=True)

        # we can show up to 10 TRs on the screen, but not having the trigger on the very last
        # row we can start the loading process before the user gets to the final TR.
        last_tr = trs[-10]
        last_tr.attrs['hx-trigger'] = 'intersect once'
        last_tr.attrs['hx-get'] = request.path + f"?{new_query_string}"
        last_tr.attrs['hx-target'] = "#tbody_id_workqueue_list"
        last_tr.attrs['hx-swap'] = 'beforeend'

    if not page:
        return HttpResponse(table)

    return HttpResponse(trs)


def assign_work(request, dataset_id):
    datasets = models.Dataset.objects.filter(pk=dataset_id)
    dataset = datasets.first()

    user_id = request.POST.get('assigned_to', None)
    if user_id:
        assign_to = User.objects.get(pk=user_id)
        dataset.status = models.DataStatus.objects.get(name__iexact="Received")
        dataset.save()

        if not hasattr(dataset, "processing"):
            processing = models.Processing.objects.create(dataset=dataset, assigned_to=assign_to)
        else:
            dataset.processing.assigned_to = assign_to
            dataset.processing.save()
    else:
        assign_to = None
        dataset.status = models.DataStatus.objects.get(name__iexact="Unknown")
        dataset.save()

        dataset.processing.delete()

    group = Group.objects.get(name__iexact="Datashop Processors")
    context = {
        'user': request.user,
        'datasets': datasets,
        'processors': User.objects.filter(groups=group),
        'csrf_token': get_token(request)
    }
    html = render_to_string('core/partial/table_work_queue.html', context)
    soup = BeautifulSoup(html, 'html.parser')
    tr = soup.find('tr', id=f'tr_id_workqueue_{dataset_id}')
    return HttpResponse(tr)


def clear_filter(request):
    context = {'filter_form': WorkQueueFilter()}
    html = render_to_string('core/partial/form_filter_work_queue.html', context=context)
    return HttpResponse(html)


urlpatterns = [
    path('workqueue', WorkQueueView.as_view(), name="workqueue_view"),
    path('workqueue/list', list_work, name="list_work"),
    path('workqueue/assign/<int:dataset_id>', assign_work, name="assign_work"),
    path('workqueue/clear_filter', clear_filter, name="clear_work_queue_filter_form")
]