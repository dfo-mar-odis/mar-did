import os
import copy

from datetime import datetime
from bs4 import BeautifulSoup

from django import forms
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

from core import models

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

def save_files(user, data, files, override=False):
    cruise_year = data.cruise.start_date.strftime('%Y')
    target_directory = os.path.join(settings.MEDIA_ROOT, cruise_year, data.cruise.name, data.data_type.name)

    # Ensure the directory exists
    os.makedirs(target_directory, exist_ok=True)

    # Create DataFile objects for each file
    for file_ in files:
        file_path = os.path.join(target_directory, file_.name)

        data_files = data.data_files.filter(file_name=file_.name)
        datafile = None
        if data_files.exists():
            if not override:
                raise FileExistsError("This file already exists")

            datafile = data_files.first()

        # Write the file to the target directory
        with open(file_path, 'wb+') as destination:
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

                notifiers = {user.email for user in users}
                notifiers.update(user.email for user in data.cruise.data_managers.all())
                notifiers.update(user.email for user in data.cruise.chief_scientists.all())
                send_mail(
                    _("Cruise update: Files added"),
                    f"{data.data_type.name} " + _("Files have been submitted to a crise") + f" [{data.cruise}]",
                    "Do.Not.Reply@mar-did.dfo-mpo.gc.ca",
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

urlpatterns = [
    path('data_submission/<int:data_id>', DataSubmissionView.as_view(), name='data_submission_view'),
    path('data_submission/<int:data_id>/<int:notify>', submit_data, name='submit_data'),
    path('data_submission/<int:data_id>/list', list_files, name='update_file_list'),
    path('clear/', HttpResponse, name='clear')
]
