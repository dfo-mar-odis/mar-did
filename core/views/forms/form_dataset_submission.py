import os

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from core import models, utils

import logging

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
        return context

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


urlpatterns = [
    path('dataset/submission/<int:dataset_id>', DatasetSubmissionView.as_view(), name='dataset_submission_view'),

    path('dataset/submission/form/clear/<int:dataset_id>', clear_submission_form, name='clear_form_dataset_submission'),

    path('dataset/submission/files/add/<int:dataset_id>', submit_files, name='submit_dataset_files'),
    path('dataset/submission/files/list/<int:dataset_id>', list_files, name='dataset_files_list'),

    path('dataset/submission/archive/<int:dataset_id>', get_archive_from, name='get_archive_form'),
]
