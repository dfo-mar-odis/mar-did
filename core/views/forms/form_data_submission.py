import os

from bs4 import BeautifulSoup

from django import forms
from django.db.models import Value
from django.db.models.functions import Concat
from django.http.request import QueryDict
from django.urls import path, reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML
from crispy_forms.bootstrap import StrictButton
from crispy_forms.utils import render_crispy_form

from core import models

import logging

logger = logging.getLogger('mardid')


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['multiple'] = True
        return context


class DataSubmissionForm(forms.ModelForm):
    files = forms.FileField(
        widget=MultipleFileInput(),
        required=False,
        label=_("Upload Files")
    )

    class Meta:
        exclude = ['legacy_file_location']
        model = models.Data

    def clean_files(self):
        files = self.files.getlist('files')
        if not files or files[0].name == '':
            raise forms.ValidationError(_("At least one file must be uploaded"))
        return files

    def clean(self):
        cleaned_data = super().clean()
        # Remove file validation logic that requires files
        uploaded_files = self.files.getlist('files')

        if uploaded_files and uploaded_files[0].name:
            cleaned_data['files'] = uploaded_files

        return cleaned_data

    def __init__(self, *args, data_object, files=None, **kwargs):
        self.files = files
        super().__init__(*args, files=files, **kwargs)
        status = models.DataStatus.objects.get(name__iexact='Received')
        self.initial['cruise'] = data_object.cruise
        self.initial['data_type'] = data_object.data_type
        self.initial['status'] = status

        self.fields['cruise'].widget = forms.HiddenInput()
        self.fields['data_type'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()

        # Add a file upload field for multiple files
        self.helper = FormHelper()
        self.helper.form_tag = False


class DataSubmissionView(TemplateView):
    template_name = 'core/form_data_submission.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_object = models.Data.objects.get(pk=self.kwargs['data_id'])
        context['data_form'] = DataSubmissionForm(data_object=data_object)
        context['cruise'] = data_object.cruise
        context['title'] = _("Cruise") + " " + str(context['cruise']) + " " + _("Data Submission")
        return context


def save_files_to_media(files):
    saved_files = []
    fs = FileSystemStorage(location=settings.MEDIA_ROOT)

    for file in files:
        filename = fs.save(file.name, file)
        saved_files.append(os.path.join(settings.MEDIA_URL, filename))

    return saved_files


def submit_data(request, data_id):
    data_object = models.Data.objects.get(pk=data_id)

    form = DataSubmissionForm(
        request.POST,
        files=request.FILES,
        data_object=data_object,
        instance=data_object
    )
    if form.is_valid():
        data = form.save()
        files = request.FILES.getlist('files')

        # Save the files
        file_paths = save_files_to_media(files)

        # Create DataFile objects for each file
        for file, path in zip(files, file_paths):
            # Assuming DataFile model has fields for file name and path
            models.DataFile.objects.create(
                data=data,
                name=file.name,
                file_path=path
            )

        return redirect(reverse_lazy('core:data_view', args=[data_object.cruise.id]))

    logger.error(form.errors)
    # If form is invalid, render form with errors
    context = {
        'data_form': form,
        'cruise': data_object.cruise,
        'data_id': data_id
    }
    html = render_to_string('core/form_data_submission.html', context, request)
    soup = BeautifulSoup(html, 'html.parser')
    return HttpResponse(soup.find('form', id='form_id_data'))


urlpatterns = [
    path('data_submission/<int:data_id>', DataSubmissionView.as_view(), name='data_submission_view'),
    path('data_submission/<int:data_id>/submit', submit_data, name='submit_data')
]
