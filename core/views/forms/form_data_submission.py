import os
import copy
import shutil

from datetime import datetime
from bs4 import BeautifulSoup

from django import forms
from django.middleware.csrf import get_token
from django.contrib.auth import models as auth_models
from django.urls import path, reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.conf import settings
from django.core.mail import send_mail
from django.core.files.storage import FileSystemStorage

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field

from core import models

from filecmp import cmp

import logging

logger = logging.getLogger('mardid')


class DataSubmissionView(TemplateView):
    template_name = 'core/form_data_submission.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data_object = models.Dataset.objects.get(pk=self.kwargs['data_id'])
        context['data_form'] = DataSubmissionForm(data_object=data_object)
        context['dataset'] = data_object
        context['title'] = _("Cruise") + " " + str(data_object.cruise) + " " + _("Data Submission")
        return context


class ArchiveFileForm(forms.ModelForm):

    class Meta:
        model = models.DataFileIssues
        fields = ['issue', 'datafile', 'submitted_by']
        widgets = {
            'datafile': forms.HiddenInput(),
            'submitted_by': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        # Add a more descriptive label for the issue field
        self.fields['issue'].label = _("Reason for archiving file")


class DataSubmissionForm(forms.ModelForm):

    class Meta:
        exclude = ['legacy_file_location']
        model = models.Dataset

    def __init__(self, *args, data_object, files=None, **kwargs):
        self.files = files
        super().__init__(*args, files=files, **kwargs)

        if not self.instance.pk:
            status = models.DataStatus.objects.get(name__iexact='expected')
        else:
            status = self.instance.status

        self.initial['instruments'] = data_object.instruments.all()
        self.initial['cruise'] = data_object.cruise
        self.initial['data_type'] = data_object.data_type
        self.initial['status'] = status

        self.fields['cruise'].widget = forms.HiddenInput()
        self.fields['data_type'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()

        # Add a file upload field for multiple files
        self.helper = FormHelper()
        self.helper.form_tag = False


def save_files_to_media(files):
    saved_files = []
    fs = FileSystemStorage(location=settings.MEDIA_ROOT)

    for file in files:
        filename = fs.save(file.name, file)
        saved_files.append(os.path.join(settings.MEDIA_URL, filename))

    return saved_files


def get_target_directory(dataset, archive: bool = False):
    cruise = dataset.cruise
    cruise_year = cruise.start_date.strftime('%Y')
    path_elements = [cruise_year, cruise.name]

    if archive:
        path_elements.append('archive')

    # TODO: Talking to Lindsay, samples should be placed in a biochem directory. This ties in with a 'DataTypePurpose'
    #   lookup I have planned. A data type prupose would be like 'Logging', 'Sample', 'Sensor', this way we can
    #   do things like require a curise to specifiy how it's going to log data (Elog, Andes, Custom CSV), or save
    #   Samples to a Biochem directory within the /Src/Mar-did/year/cruise/Biochem

    # I would use the purpose.id for this, but using a string is more clear for humans.
    # data_purpose = dataset.data_type.purpose
    # if purpose.name.lower() == 'Sample':
    #   path_elements.append('Biochem')
    return os.path.join(*path_elements, dataset.data_type.name)


def save_files(user, data, files, override=False):
    target_directory = get_target_directory(data)

    # Create DataFile objects for each file
    for file_ in files:
        media_path = os.path.join(settings.MEDIA_ROOT, target_directory)

        # Ensure the directory exists
        os.makedirs(media_path, exist_ok=True)

        file_path = os.path.join(target_directory, file_.name)
        media_file_path = os.path.join(media_path, file_.name)
        data_files = data.files.filter(file=media_file_path)
        datafile = None
        if data_files.exists():
            if not override:
                raise FileExistsError("This file already exists")

            # Todo: if the file already exists, and the user has chosen to override it, then we sould archive the
            #   old file in an archive folder. At that point we can ask the user why they uploaded a new file and
            #   save the response to the DataFileIssues table attached to the archived file.
            #   Or,
            #   we don't allow the user to upload the file until they've manually archived the old file with
            #   an explination as to why they archived it.
            datafile = data_files.first()

        # Write the file to the target directory
        with open(media_file_path, 'wb+') as destination:
            for chunk in file_.chunks():
                destination.write(chunk)

        if datafile:
            datafile.file = file_path
            datafile.submitted_by=user
            datafile.save()
            continue

        # Assuming DataFile model has fields for file name and path
        models.DataFiles.objects.create(
            data=data,
            file=file_path,
            file_name=file_.name,
            submitted_by=user
        )


def submit_data(request, data_id, notify):
    data_object = models.Dataset.objects.get(pk=data_id)

    form = DataSubmissionForm(
        request.POST,
        files=request.FILES,
        data_object=data_object,
        instance=data_object
    )

    context = {
        'data_form': form,
        'dataset': data_object,
    }

    if form.is_valid():
        data = form.save()
        html = render_to_string('core/form_data_submission.html', context, request)
        soup = BeautifulSoup(html, 'html.parser')

        files = request.FILES.getlist('files')
        if files:
            try:
                # if the files already exist, we need to check with the user that it's ok to override them
                # Todo: This is where
                override = request.POST.get('override', False)
                save_files(request.user, data, files, override=override)
            except FileExistsError as ex:
                soup_return = BeautifulSoup('', 'html.parser')
                form = soup.find('form', id='form_id_data')

                submit_button = soup.find('button', id="btn_id_form_submit").extract()
                submit_button.attrs['hx-swap-oob'] = 'true'

                submit = submit_button.find('span')
                # this is a tricky trick. We want the user to confirm if they want to override the existing files
                # so we add a hidden input that triggers a resubmit for the form when it's swap it into the DOM
                # that asks the user to confirm if they want to override the files. But if we leave it there the
                # next time they click the button the input will be present and we'll be assuming override == true
                # so we'll put the input in a div, that will delete itself right after it's loaded in the DOM
                # Next time the user clicks the submit button it'll be like they were submitting for the first time
                submit.append(input_div:=soup.new_tag("div", attrs={'class': 'd-none'}))
                input_div.attrs['hx-get'] = reverse_lazy('core:clear')
                input_div.attrs['hx-swap'] = 'delete'
                input_div.attrs['hx-trigger'] = 'load'

                input_div.append(input:=soup.new_tag("input"))
                input.attrs['type'] = 'hidden'
                input.attrs['name'] = 'override'
                input.attrs['value'] = 'override'
                input.attrs['hx-post'] = request.path
                input.attrs['hx-confirm'] = _("These files already exist, are you sure you wish to override them?")
                input.attrs['hx-trigger'] = 'load'

                soup_return.append(submit_button)
                return HttpResponse(soup_return)

        if notify:
            if int(notify) == 1:
                data.status = models.DataStatus.objects.get(name__iexact='lab')
                data.save()
            elif int(notify) == 2:
                data.status = models.DataStatus.objects.get(name__iexact='submitted')
                data.save()
                group = auth_models.Group.objects.get(name__iexact='Datashop Processors')
                users = auth_models.User.objects.filter(groups=group)

                notifiers = {request.user.email}
                notifiers = {user.email for user in users}
                notifiers.update(user.email for user in data.cruise.data_managers.all())
                notifiers.update(user.email for user in data.cruise.chief_scientists.all())
                # remove blanks for ppl that didn't have an email
                if '' in notifiers:
                    notifiers.remove('')
                send_mail(
                    _("Cruise update: Files added"),
                    f"{data.data_type.name} " + _("Files have been submitted for cruise") + f" [{data.cruise}]",
                    _("Do.Not.Reply@mar-did.dfo-mpo.gc.ca"),
                    notifiers
                )

        response = HttpResponse()
        response['HX-Redirect'] = reverse_lazy('core:data_submission_view', args=[data.pk])
        return response

    logger.error(form.errors)

    html = render_to_string('core/form_data_submission.html', context, request)
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form', id='form_id_data')
    form.attrs['hx-swap-oob'] = 'true'
    return HttpResponse(form)


def list_files(request, data_id):
    data_object = models.Dataset.objects.get(pk=data_id)
    context = {'dataset': data_object}
    html = render_to_string('core/form_data_submission.html', context)
    soup = BeautifulSoup(html, 'html.parser')
    return HttpResponse(soup.find('div', id='div_id_file_list'))


def get_archive_form(request, datafile_id):

    datafile = models.DataFiles.objects.get(pk=datafile_id)
    initial = {
        'submitted_by': request.user.id,
        'datafile': datafile
    }
    context = {
        'datafile_id': datafile_id,
        'archive_form': ArchiveFileForm(initial=initial),
        'csrf_token': get_token(request)
    }
    html = render_to_string('core/partials/form_archive_file.html', context=context)
    return HttpResponse(html)


def archive(request, datafile_id):

    file = models.DataFiles.objects.get(pk=datafile_id)

    datafile = models.DataFiles.objects.get(pk=datafile_id)
    initial = {
        'submitted_by': request.user,
        'datafile': datafile,
        'issue': request.POST.get('issue')
    }
    form = ArchiveFileForm(request.POST)
    if form.is_valid():
        issue = form.save()
        dataset = file.data

        current_file_path = get_target_directory(dataset)
        archive_file_path = get_target_directory(dataset, archive=True)

        media_current_path = os.path.join(settings.MEDIA_ROOT, current_file_path)
        media_archive_path = os.path.join(settings.MEDIA_ROOT, archive_file_path)

        # Ensure the archive path exists
        os.makedirs(media_archive_path, exist_ok=True)

        archived_file = os.path.join(archive_file_path, file.file_name)

        media_current_file = os.path.join(media_current_path, file.file_name)
        media_archived_file = os.path.join(media_archive_path, file.file_name)
        shutil.move(media_current_file, media_archived_file)

        # Update the file path in the database
        file.file = archived_file
        file.save()

        response = HttpResponse()
        response['HX-Trigger'] = 'update_file_list'
        return response

    context = {
        'datafile_id': datafile_id,
        'archive_form': form,
        'csrf_token': get_token(request)
    }
    html = render_to_string('core/partials/form_archive_file.html', context=context)
    return HttpResponse(html)

urlpatterns = [
    path('data_submission/<int:data_id>', DataSubmissionView.as_view(), name='data_submission_view'),
    path('data_submission/<int:data_id>/<int:notify>', submit_data, name='submit_data'),
    path('data_submission/<int:data_id>/list', list_files, name='update_file_list'),
    path('data_submission/archive/form/<int:datafile_id>', get_archive_form, name='get_archive_form'),
    path('data_submission/archive/<int:datafile_id>', archive, name='archive_file'),
    path('clear/', HttpResponse, name='clear')
]
