import os

from bs4 import BeautifulSoup
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, Row, Column, Div, Field
from crispy_forms.utils import render_crispy_form
from django.conf import settings
from django.contrib.auth.models import User
from django.forms import ModelForm
from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.template.loader import render_to_string
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from pandas.io.sas.sas_constants import dataset_length, dataset_offset

from core import models, utils

import logging

from core.models import Datasets

logger = logging.getLogger('mardid')


class DatasetSubmissionView(TemplateView):
    template_name = 'core/forms/form_dataset_submission.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_object = models.Datasets.objects.get(pk=self.kwargs['dataset_id'])

        # You can't setup crispy forms with a proper file upload dialog so we're going to have to
        # create the form using HTML. I've left this here commented out so future devs will know
        # why this form is handled differently from other forms.
        # context['file_submission_form'] = FileSubmissionForm(data_object)
        context['dataset'] = data_object
        context['status_form'] = DatasetSubmissionStatusForm(instance=data_object)
        context['dataset_comments_form'] = DatasetCommentsForm(data_object, self.request.user)
        return context


class DatasetSubmissionStatusForm(ModelForm):
    class Meta:
        model = models.Datasets
        fields = ['status']
        labels = {
            'status': _('Dataset Status'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['status'].initial = self.instance.status.pk

        self.helper = FormHelper()
        self.helper.form_tag = False

        submit_url = reverse_lazy('core:update_dataset_status_form', args=[self.instance.id])

        btn_submit_attrs = {
            'title': _("Update Status"),
            'hx-target': "#form_id_dataset_status",
            'hx-swap': "innerHTML",
            'hx-post': submit_url
        }

        btn_label = _("Update Status")
        btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label}',
                                  css_class='btn btn-primary mb-1',
                                  **btn_submit_attrs)

        self.helper.layout = Layout(
            Hidden('dataset', self.instance.pk),
            Div(
                Row(
                    Column(Field('status'), css_class='form-control-sm'),
                ),
                Div(
                    btn_submit
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            ),
        )
        

class DatasetCommentsForm(ModelForm):
    class Meta:
        model = models.DatasetComments
        fields = '__all__'

    def __init__(self, dataset: models.Datasets, author: User, *args, **kwargs):
        dataset_id = dataset.pk if dataset is not None else -1

        initial = kwargs.pop('initial') if 'initial' in kwargs else {}

        super(DatasetCommentsForm, self).__init__(initial=initial, *args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Hidden('dataset', dataset_id),
                Hidden('author', author.pk),
                Row(
                    Column(Field('comment'), css_class='form-control-sm'),
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            )
        )

        if dataset_id > 0:
            if self.instance.pk:
                submit_url = reverse_lazy('core:update_dataset_comment', args=[dataset_id, self.instance.pk])
            else:
                submit_url = reverse_lazy('core:add_dataset_comment', args=[dataset_id])

            button_div = Div()
            btn_submit_attrs = {
                'title': _("Add Comment"),
                'hx-target': "#form_id_dataset_comments",
                'hx-post': submit_url
            }

            btn_label = _("Add Comment")
            btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label}',
                                      css_class='btn btn-sm btn-primary mb-1',
                                      **btn_submit_attrs)
            button_div.append(btn_submit)
            self.helper.layout.fields[0].fields.append(button_div)


def get_file_path(dataset: models.Datasets, datatype_output: str):
    return os.path.join(settings.MEDIA_OUT, dataset.get_dataset_root_path, datatype_output)

def save_files(user: User, dataset: models.Datasets, files):

    datatype_output = dataset.data_type.locations.first().output_dir
    output_path = str(get_file_path(dataset, datatype_output))

    if len(files) > 0:
        if not os.path.exists(output_path):
            # Create the directory
            os.makedirs(output_path)
            print(f"Directory created: {output_path}")
        else:
            print(f"Directory already exists: {output_path}")

        file_type = models.FileTypes.objects.get_or_create(extension=".tst", description="this is for testing purposes")[0]
        for file in files:
            file_path = os.path.join(output_path, file.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)

            models.DataFiles.objects.create(dataset=dataset, file_name=file.name, file_type=file_type, submitted_by=user, is_archived=False)
            logger.info(f"File saved: {file_path}")


def submit_files(request, dataset_id):
    if response:=utils.redirect_if_not_authenticated(request):
        return response

    if request.method == 'POST':
        post_vars = request.POST.copy()
        files = request.FILES.getlist('files')

        dataset = models.Datasets.objects.get(pk=dataset_id)
        save_files(request.user, dataset, files)

        response = HttpResponse()
        response['HX-Trigger'] = "dataset_files_updated"
        return response

    return HttpResponse()


def get_archive_from(request, dataset_id):
    return HttpResponse()


def list_files(request, dataset_id):
    dataset = models.Datasets.objects.get(pk=dataset_id)
    files = dataset.files.filter(is_archived=False)

    file_list_html = render_to_string('core/partials/table_dataset_files.html', context={'dataset': dataset, 'files': files}, request=request)
    soup = BeautifulSoup(file_list_html, 'html.parser')
    table = soup.find('table')
    table.attrs['hx-trigger'] = "dataset_files_updated from:body"

    return HttpResponse(soup)


def clear_submission_form(request, dataset_id):
    dataset = models.Datasets.objects.get(pk=dataset_id)

    form = render_to_string('core/partials/form_dataset_submission.html', context={'dataset': dataset}, request=request)
    soup = BeautifulSoup(form, 'html.parser')
    return HttpResponse(soup.find('form'))


def update_dataset_status_form(request, dataset_id):
    dataset = models.Datasets.objects.get(pk=dataset_id)

    form = DatasetSubmissionStatusForm(request.POST, instance=dataset)
    if form.is_valid():
        form.save()

        context = {
            'csrf_token': get_token(request)  # Add CSRF token to the context
        }
        form = DatasetSubmissionStatusForm(instance=dataset)
        response = HttpResponse(render_crispy_form(form, context=context))
        response['HX-Trigger'] = "dataset_status_updated"
        return response

    return form


def update_dataset_status(request, dataset_id):

    dataset = models.Datasets.objects.get(pk=dataset_id)

    soup = BeautifulSoup('', 'html.parser')
    soup.append(span:=soup.new_tag('span', attrs={'id': "span_id_submission_status"}))
    span.attrs['hx-get'] = reverse_lazy('core:update_dataset_status', args=[dataset_id])
    span.attrs['hx-trigger'] = "dataset_status_updated from:body"
    span.attrs['hx-swap'] = "outerHTML"
    span.attrs['class'] = f'btn btn-sm {dataset.status.get_button_colour} text-black'
    span.string = dataset.status.name

    return HttpResponse(soup)


# used to clear or populate a form
def dataset_comment_form(request, dataset_id, **kwargs):
    if 'comment_id' in kwargs:
        comment_id = int(kwargs.get('comment_id'))
        comment = models.DatasetComments.objects.get(pk=comment_id)
        dataset = comment.dataset
        form = DatasetCommentsForm(dataset, request.user, instance=comment)
    else:
        dataset = models.Datasets.objects.get(pk=dataset_id)
        form = DatasetCommentsForm(dataset, request.user)

    html = render_crispy_form(form)
    return HttpResponse(html)


def dataset_comment_update(request, dataset_id, **kwargs):
    if response := utils.redirect_if_not_authenticated(request):
        return response

    # Create a mutable copy of the POST data
    post_data = request.POST.copy()

    dataset = models.Datasets.objects.get(pk=dataset_id)
    if 'comment_id' in kwargs:
        comment_id = int(kwargs.get('comment_id'))
        dataset_comment = models.DatasetComments.objects.get(pk=comment_id)
        form = DatasetCommentsForm(dataset, request.user, post_data, instance=dataset_comment)
    else:
        form = DatasetCommentsForm(dataset, request.user, post_data)

    if form.is_valid():
        try:
            form.save()
            form = DatasetCommentsForm(dataset, request.user)
            crispy = render_crispy_form(form)
            soup = BeautifulSoup(crispy, 'html.parser')

            response = HttpResponse(soup)
            response['HX-Trigger'] = 'dataset_comment_updated'
            return response
        except Exception as ex:
            logger.error("Failed to save the mission comment form.")
            logger.exception(ex)
            form.add_error(None, _("An unexpected error occurred while saving the form."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


def dataset_comment_list(request, dataset_id):
    dataset = models.Datasets.objects.get(pk=dataset_id)

    context = {
        'dataset': dataset,
        'user': request.user
    }
    html = render_to_string('core/partials/table_dataset_comments.html', context=context, request=request)
    return HttpResponse(html)


def dataset_comment_delete(request, dataset_id, comment_id):
    if response := utils.redirect_if_not_authenticated(request):
        return response

    comment = models.DatasetComments.objects.get(pk=comment_id)
    comment.delete()

    return HttpResponse()


urlpatterns = [
    path('dataset/submission/<int:dataset_id>', DatasetSubmissionView.as_view(), name='dataset_submission_view'),

    path('dataset/submission/form/clear/<int:dataset_id>', clear_submission_form, name='clear_form_dataset_submission'),

    path('dataset/submission/status/update/<int:dataset_id>', update_dataset_status_form, name='update_dataset_status_form'),
    path('dataset/submission/status/update/icon/<int:dataset_id>', update_dataset_status,
         name='update_dataset_status'),

    path('dataset/submission/files/add/<int:dataset_id>', submit_files, name='submit_dataset_files'),
    path('dataset/submission/files/list/<int:dataset_id>', list_files, name='dataset_files_list'),

    path('dataset/submission/archive/<int:dataset_id>', get_archive_from, name='get_archive_form'),

    path('dataset/comment/add/<int:dataset_id>', dataset_comment_update, name='add_dataset_comment'),
    path('dataset/comment/add/<int:dataset_id>/<int:comment_id>', dataset_comment_update,
         name='update_dataset_comment'),
    path('dataset/comment/remove/<int:dataset_id>/<int:comment_id>', dataset_comment_delete,
         name='delete_dataset_comment'),
    path('dataset/comment/update/<int:dataset_id>/<int:comment_id>', dataset_comment_form, name='dataset_comment_form'),
    path('dataset/comment/list/<int:dataset_id>', dataset_comment_list, name='list_dataset_comments'),
]
