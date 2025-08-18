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

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML
from crispy_forms.bootstrap import StrictButton
from crispy_forms.utils import render_crispy_form

from core import models

import logging

logger = logging.getLogger('mardid')


class DataSubmissionForm(forms.ModelForm):

    class Meta:
        exclude = ['legacy_file_location']
        model = models.Data

    def __init__(self, *args, data, **kwargs):
        super().__init__(*args, **kwargs)
        status = models.DataStatus.objects.get(name__iexact='Received')
        self.initial['cruise'] = data.cruise
        self.initial['data_type'] = data.data_type
        self.initial['status'] = status

        self.fields['cruise'].widget = forms.HiddenInput()
        self.fields['data_type'].widget = forms.HiddenInput()
        self.fields['status'].widget = forms.HiddenInput()


class DataSubmissionView(TemplateView):
    template_name = 'core/form_data_submission.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        data = models.Data.objects.get(pk=self.kwargs['data_id'])
        context['data_form'] = DataSubmissionForm(data=data)
        context['cruise'] = data.cruise
        context['title'] = _("Cruise") + " " + str(context['cruise']) + " " + _("Data Submission")
        return context



urlpatterns = [
    path('data_submission/<int:data_id>', DataSubmissionView.as_view(), name='data_submission_view')
]