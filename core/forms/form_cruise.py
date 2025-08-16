from bs4 import BeautifulSoup

from django import forms
from django.urls import path, reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.http.response import HttpResponse, HttpResponseRedirect
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML
from crispy_forms.bootstrap import StrictButton
from crispy_forms.utils import render_crispy_form

from core import models

import logging

logger = logging.getLogger('mardid')


class CruiseForm(forms.ModelForm):
    chief_scientists_select = forms.ModelChoiceField(
        queryset=models.Contacts.objects.none(),
        label="Select Chief Scientist",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    chief_scientists = forms.ModelMultipleChoiceField(
        queryset=models.Contacts.objects.none(),
        label="Chief Scientists"
    )
    locations_select = forms.ModelChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        label="Select Geographic Locations",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    locations = forms.ModelMultipleChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        label="Geographic Locations"
    )

    class Meta:
        model = models.Cruises
        fields = '__all__'
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
        }

    def clean_chief_scientists(self):
        chief_scientists = self.cleaned_data.get('chief_scientists')

        # Example validation: Ensure at least one chief scientist is selected
        if not chief_scientists or not chief_scientists.exists():
            self.add_error(None, _("At least one chief scientist must be added."))  # Non-field error
            self.fields['chief_scientists_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return chief_scientists

    def clean_locations(self):
        locations = self.cleaned_data.get('locations')

        # Example validation: Ensure at least one chief scientist is selected
        if not locations or not locations.exists():
            self.add_error(None, _("At least one geographic location must be added."))  # Non-field error
            self.fields['locations_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return locations

    def init_scientists(self):
        scientists_list = ""
        scientists = [con.id for con in self.instance.chief_scientists.all()] if self.instance.pk else []

        if not scientists:
            if self.data and 'chief_scientists_bullet' in self.data:
                scientists = self.data.getlist('chief_scientists_bullet')

        for scientist_id in scientists:
            scientists_list += get_scientists_bullet(scientist_id)

        # Filter chief scientists to only include contacts with the "chief scientists" role
        chief_scientist_role = models.ContactRoles.objects.filter(name__iexact='chief scientist').first()
        if chief_scientist_role:
            self.fields['chief_scientists_select'].queryset = models.Contacts.objects.filter(roles=chief_scientist_role)
            self.fields['chief_scientists'].queryset = models.Contacts.objects.filter(roles=chief_scientist_role)

        return scientists_list

    def init_locations(self):
        locations_list = ""
        locations = [loc.id for loc in self.instance.locations.all()] if self.instance.pk else []
        if not locations:
            if self.data and 'locations_bullet' in self.data:
                locations = self.data.getlist('locations_bullet')

        for location_id in locations:
            locations_list += get_location_bullet(location_id)

        self.fields['locations_select'].queryset = models.GeographicRegions.objects.all()
        self.fields['locations'].queryset = models.GeographicRegions.objects.all()

        return locations_list

    def __init__(self, *args, **kwargs):

        super(CruiseForm, self).__init__(*args, **kwargs)

        scientists_list = self.init_scientists()
        locations_list = self.init_locations()

        btn_add_scientist_attrs = {
            'hx-target': "#div_id_cheif_scientists",
            'hx-post': reverse_lazy('core:add_chief_scientist'),
            'hx-swap': "beforeend"
        }

        btn_add_scientist = StrictButton('<span class="bi bi-plus-square"></span>',
                                         css_class='btn btn-sm btn-primary mb-1',
                                         **btn_add_scientist_attrs)

        btn_add_location_attrs = {
            'hx-target': "#div_id_locations",
            'hx-post': reverse_lazy('core:add_location'),
            'hx-swap': "beforeend"
        }

        btn_location = StrictButton('<span class="bi bi-plus-square"></span>',
                                    css_class='btn btn-sm btn-primary mb-1',
                                    **btn_add_location_attrs)

        submit_url = (reverse_lazy('core:update_cruise', args=[self.instance.pk])
                      if self.instance.pk else
                      reverse_lazy('core:add_cruise'))
        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_id_cruise",
            'hx-post': submit_url
        }

        btn_submit = StrictButton('<span class="bi bi-check-square"></span>',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_submit_attrs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Row(
                Column(Field('name'), css_class='form-control-sm'),
                Column(Field('descriptor'), css_class='form-control-sm'),
            ),
            Row(
                Column(Field('start_date'), css_class='form-control-sm'),
                Column(Field('end_date'), css_class='form-control-sm'),
            ),
            Row(
                Column(
                    Field('chief_scientists_select', wrapper_class='d-inline-block'),
                    btn_add_scientist,
                    css_class='form-control-sm'
                ),
            ),
            Row(
                Field('chief_scientists', wrapper_class="d-none"),
                HTML(scientists_list),
                id='div_id_cheif_scientists',
            ),
            Row(
                Column(
                    Field('locations_select', wrapper_class='d-inline-block'),
                    btn_location,
                    css_class='form-control-sm'
                ),
            ),
            Row(
                Field('locations', wrapper_class="d-none"),
                HTML(locations_list),
                id='div_id_locations',
            ),
            btn_submit
        )


class CreateCruise(LoginRequiredMixin, TemplateView):
    template_name = 'core/form_cruise.html'
    login_url = reverse_lazy('login')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Create Cruise')
        if 'cruise_id' in self.kwargs:
            context['object'] = models.Cruises.objects.get(pk=self.kwargs['cruise_id'])
            context['cruise_form'] = CruiseForm(instance=context['object'])
        else:
            context['cruise_form'] = CruiseForm()

        return context


def get_scientists_bullet(contact_id):
    scientist = models.Contacts.objects.get(pk=contact_id)

    context = {
        'input_name': 'chief_scientists_bullet',
        'value_id': scientist.pk,
        'value_label': str(scientist),
        'post_url': reverse_lazy('core:remove_chief_scientist', args=[scientist.pk]),
    }
    return render_to_string('core/partial/multi_select_bullet.html', context=context)


def get_updated_scientists_list(scientists_ids: [int]):
    form = CruiseForm(initial={'chief_scientists': scientists_ids})
    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    scientist_select = form_soup.find(id="id_chief_scientists")
    scientist_select.attrs['hx-swap'] = 'outerHTML'
    scientist_select.attrs['hx-swap-oob'] = 'true'

    return scientist_select


def add_chief_scientist(request):
    new_scientist_id = request.POST.get('chief_scientists_select')

    existing = request.POST.getlist('chief_scientists_bullet')
    if new_scientist_id in existing:
        return HttpResponse()

    soup = BeautifulSoup()

    new_pill = get_scientists_bullet(new_scientist_id)

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    existing_ids.append(int(new_scientist_id))

    soup.append(get_updated_scientists_list(existing_ids))
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return HttpResponse(soup)


def remove_chief_scientist(request, scientist_id):
    existing_ids = [int(id) for id in request.POST.getlist('chief_scientists')]
    if scientist_id not in existing_ids:
        return HttpResponse()

    soup = BeautifulSoup()

    existing_ids.remove(scientist_id)
    soup.append(get_updated_scientists_list(existing_ids))

    return HttpResponse(soup)


def get_location_bullet(location_id):
    location = models.GeographicRegions.objects.get(pk=location_id)

    context = {
        'input_name': 'locations_bullet',
        'value_id': location.pk,
        'value_label': str(location),
        'post_url': reverse_lazy('core:remove_location', args=[location.pk]),
    }
    return render_to_string('core/partial/multi_select_bullet.html', context=context)


def get_updated_location_list(location_ids: [int]):
    form = CruiseForm(initial={'locations': location_ids})
    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    scientist_select = form_soup.find(id="id_locations")
    scientist_select.attrs['hx-swap'] = 'outerHTML'
    scientist_select.attrs['hx-swap-oob'] = 'true'

    return scientist_select


def add_location(request):
    new_location_id = request.POST.get('locations_select')

    existing = request.POST.getlist('locations_bullet')
    if new_location_id in existing:
        return HttpResponse()

    soup = BeautifulSoup()

    new_pill = get_location_bullet(new_location_id)

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    existing_ids.append(int(new_location_id))

    soup.append(get_updated_location_list(existing_ids))
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return HttpResponse(soup)


def remove_location(request, location_id):
    existing_ids = [int(id) for id in request.POST.getlist('locations')]
    if location_id not in existing_ids:
        return HttpResponse()

    soup = BeautifulSoup()

    existing_ids.remove(location_id)
    soup.append(get_updated_location_list(existing_ids))

    return HttpResponse(soup)


def add_cruise(request):
    form = CruiseForm(request.POST)

    if form.is_valid():
        try:
            cruise = form.save()
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('core:update_cruise_view', args=[cruise.id])
            return response
        except Exception as ex:
            logger.error("Failed to save the cruise form.")
            logger.exception(ex)
            form.add_error(None,
                           _("An unexpected error occurred while saving the form. Please contact the system administrator."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


@login_required
def update_cruise(request, **kwargs):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))  # Redirect to the login page if not authenticated

    if 'cruise_id' in kwargs:
        cruise_id = int(kwargs.get('cruise_id'))
        cruise = models.Cruises.objects.get(pk=cruise_id)
        form = CruiseForm(request.POST, instance=cruise)
    else:
        form = CruiseForm(request.POST)

    if form.is_valid():
        try:
            cruise = form.save()
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('core:update_cruise_view', args=[cruise.id])
            return response
        except Exception as ex:
            logger.error("Failed to save the cruise form.")
            logger.exception(ex)
            form.add_error(None,
                           _("An unexpected error occurred while saving the form. Please contact the system administrator."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


urlpatterns = [
    path('cruise/new', CreateCruise.as_view(), name='new_cruise_view'),
    path('cruise/<int:cruise_id>', CreateCruise.as_view(), name='update_cruise_view'),
    path('cruise/add-cruise', add_cruise, name='add_cruise'),
    path('cruise/update/<int:cruise_id>', update_cruise, name='update_cruise'),
    path('cruise/add-chief-scientist', add_chief_scientist, name='add_chief_scientist'),
    path('cruise/remove-chief-scientist/<int:scientist_id>', remove_chief_scientist, name='remove_chief_scientist'),
    path('cruise/add-location', add_location, name='add_location'),
    path('cruise/remove-location/<int:location_id>', remove_location, name='remove_location'),
]
