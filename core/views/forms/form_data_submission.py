import os
import shutil
import datetime

from datetime import datetime
from bs4 import BeautifulSoup

from django import forms
from django.middleware.csrf import get_token
from django.contrib.auth import models as auth_models
from django.urls import path, reverse_lazy
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
from core.components import get_notification_alert

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


def get_target_directory(dataset, archive: bool = False):
    cruise = dataset.cruise
    cruise_year = cruise.start_date.strftime('%Y')
    decade_folder = cruise_year[:3] + '0'
    path_elements = [decade_folder, cruise_year, cruise.name]

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


def save_files(user, dataset, files, override=False):
    logger = logging.getLogger(f'mardid.notifier{user.pk}')
    target_directory = get_target_directory(dataset)
    media_path = os.path.join(settings.MEDIA_ROOT, target_directory)

    created_files_buffer = []
    could_not_write_buffer = []

    loading_msg = _("Loading")
    fs = FileSystemStorage(location=media_path)
    for uploaded_file in files:
        logger.info(loading_msg + f" : {uploaded_file.name}")

        file_path = os.path.join(target_directory, uploaded_file.name)
        media_file_path = os.path.join(media_path, uploaded_file.name)
        if dataset.files.filter(file=file_path).exists():
            could_not_write_buffer.append(uploaded_file)
            continue

        fn = fs.save(uploaded_file.name, uploaded_file)
        mfp = fs.path(fn)

        created_files_buffer.append(
            models.DataFiles(
                data=dataset,
                file=file_path,
                file_name=uploaded_file.name,
                submitted_by=user
            )
        )

    models.DataFiles.objects.bulk_create(created_files_buffer)
    return could_not_write_buffer


def submit_data(request, data_id, notify):

    logger = logging.getLogger(f'mardid.notifier{request.user.id}')
    soup = BeautifulSoup('', 'html.parser')
    if request.method == "GET":
        soup.append(div_container:=soup.new_tag("div"))
        div_container.attrs['id'] = "div_id_data_submission_messages"
        div_container.attrs['hx-swap-oob'] = "true"
        div_container.attrs['class'] = "mt-2"

        notification = get_notification_alert(logger)
        div_container.append(notification)

        response = HttpResponse(soup)
        response['HX-Trigger'] = 'submit_form'
        return response

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
            override = request.POST.get('override', False)
            could_not_override = save_files(request.user, data, files, override=override)
            if could_not_override:
                soup = BeautifulSoup('<div class="mt-2" id="div_id_data_submission_messages"></div>', 'html.parser')
                html = ""
                # for now we're just printing an error saying the file couldn't be uploaded,
                # But AI assures me we could send the file back in a form, which could include
                # an issue text input for the DataFileIssues model, and have the file re-submitted
                # if the user wanted to archive it.
                for idx, file in enumerate(could_not_override):
                    context = {
                        'alert_id': f'file_alert_{idx}',
                        'alert_type': 'danger',
                        'message': f"{file.name} " + _("already exists. If intended, please archive the existing file with reasoning first and try uploading again.")
                    }
                    html += render_to_string('core/partials/components/template_alert.html', context)

                div = soup.find('div', id="div_id_data_submission_messages")
                div.attrs['hx-swap-oob'] = True
                div.append(BeautifulSoup(html, 'html.parser'))
                response = HttpResponse(soup)
                response['HX-Trigger'] = 'update_file_list'
                return response

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

        # we have to clear the notification dialog
        notification = get_notification_alert(logger, swap_oob=True)

        response = HttpResponse(notification)
        response['HX-Redirect'] = reverse_lazy('core:data_submission_view', args=[data.pk])
        return response

    logger.error(form.errors)

    html = render_to_string('core/form_data_submission.html', context, request)
    soup = BeautifulSoup(html, 'html.parser')
    form = soup.find('form', id='form_id_data')
    form.attrs['hx-swap-oob'] = 'true'

    notification = get_notification_alert(logger, swap_oob=True)
    form.append(notification)

    return HttpResponse(form)


def list_files(request, data_id):
    data_object = models.Dataset.objects.get(pk=data_id)
    context = {'archive_table': False, 'files': data_object.current_files}
    html = render_to_string('core/partials/table_dataset_files.html', context)
    return HttpResponse(html)


def list_archive_files(request, data_id):
    data_object = models.Dataset.objects.get(pk=data_id)
    context = {'archive_table': True, 'files': data_object.archived_files}
    html = render_to_string('core/partials/table_dataset_files.html', context)
    return HttpResponse(html)


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

        archived_file_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.file_name}"
        archived_file = os.path.join(archive_file_path, archived_file_name)
        media_current_file = os.path.join(media_current_path, file.file_name)
        media_archived_file = os.path.join(media_archive_path, archived_file_name)
        shutil.move(media_current_file, media_archived_file)

        # Update the file path in the database
        file.file = archived_file
        file.is_archived = True
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
    path('data_submission/archive<int:data_id>/list', list_archive_files, name='update_archive_file_list'),
    path('data_submission/archive/form/<int:datafile_id>', get_archive_form, name='get_archive_form'),
    path('data_submission/archive/<int:datafile_id>', archive, name='archive_file'),
    path('clear/', HttpResponse, name='clear')
]
