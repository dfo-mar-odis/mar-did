from bs4 import BeautifulSoup

from django import forms
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
from crispy_forms.layout import Layout, Div, Row, Column, Field, HTML
from crispy_forms.bootstrap import StrictButton, FieldWithButtons
from crispy_forms.utils import render_crispy_form

from core import models

import logging

logger = logging.getLogger('mardid')




class CreateCruise(LoginRequiredMixin, TemplateView):
    template_name = 'core/form_cruise.html'
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name__in=['Chief Scientists', 'MarDID Maintainers']).exists():
            return redirect(reverse_lazy('login'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Create Cruise')
        if 'cruise_id' in self.kwargs:
            context['object'] = models.Cruises.objects.get(pk=self.kwargs['cruise_id'])
            context['cruise_form'] = CruiseForm(instance=context['object'])
        else:
            context['cruise_form'] = CruiseForm()

        return context


class CruiseForm(forms.ModelForm):
    programs_select = forms.ModelChoiceField(
        queryset=models.Programs.objects.none(),
        label="Select a program",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    programs = forms.ModelMultipleChoiceField(
        queryset=models.Programs.objects.none(),
        label="Programs"
    )
    chief_scientists_select = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Select Chief Scientist",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    chief_scientists = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        label="Chief Scientists"
    )
    data_managers_select = forms.ModelChoiceField(
        queryset=User.objects.none(),
        label="Select Data Managers",
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    data_managers = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Data Managers"
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

    def clean_chief_scientists_field(self):
        chief_scientists_select = self.data.get('chief_scientists_select')
        chief_scientists = self.data.getlist('chief_scientists_bullet')

        keys = [int(contact) for contact in chief_scientists]
        if chief_scientists_select:
            keys.append(int(chief_scientists_select))

        cleaned_chief_scientists = User.objects.filter(pk__in=keys)

        # Example validation: Ensure at least one chief scientist is selected
        if not cleaned_chief_scientists.exists():
            self.add_error('chief_scientists_select', _("At least one chief scientist must be added."))  # Non-field error
            self.fields['chief_scientists_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return cleaned_chief_scientists

    def clean_data_managers_field(self):
        data_managers_select = self.data.get('data_managers_select')
        data_managers = self.data.getlist('data_managers_bullet')

        keys = [int(contact) for contact in data_managers]
        if data_managers_select:
            keys.append(int(data_managers_select))

        cleaned_data_managers = User.objects.filter(pk__in=keys)

        return cleaned_data_managers

    def clean_locations_field(self):
        locations_select = self.data.get('locations_select')
        locations = self.data.getlist('locations_bullet')

        keys = [int(location) for location in locations]
        if locations_select:
            keys.append(int(locations_select))

        cleaned_locations = models.GeographicRegions.objects.filter(pk__in=keys)

        # Example validation: Ensure at least one chief scientist is selected
        if not cleaned_locations.exists():
            self.add_error('locations_select', _("At least one geographic location must be added."))  # Non-field error
            self.fields['locations_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return cleaned_locations

    def clean_programs_field(self):
        programs_select = self.data.get('programs_select')
        programs = self.data.getlist('programs_bullet')

        keys = [int(program) for program in programs]
        if programs_select:
            keys.append(int(programs_select))

        cleaned_programs = models.Programs.objects.filter(pk__in=keys)

        # Example validation: Ensure at least one chief scientist is selected
        if not cleaned_programs.exists():
            self.add_error('programs_select', _("At least one program must be added."))  # Non-field error
            self.fields['programs_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return cleaned_programs

    def clean_chief_scientists(self):
        return self.clean_chief_scientists_field()

    def clean_chief_scientists_select(self):
        return self.clean_chief_scientists_field()

    def clean_locations_select(self):
        return self.clean_locations_field()

    def clean_locations(self):
        return self.clean_locations_field()

    def clean_programs_select(self):
        return self.clean_programs_field()

    def clean_programs(self):
        return self.clean_programs_field()

    def clean(self):
        cleaned_data = super().clean()
        cleaned_data['data_managers'] = self.clean_data_managers_field()
        return cleaned_data

    def get_list_add_btn(self, prefix):
        btn_add_attrs = {
            'hx-target': f"#div_id_{prefix}",
            'hx-post': reverse_lazy('core:add_to_list', args=[prefix]),
            'hx-swap': "beforeend"
        }

        btn_add = StrictButton('<span class="bi bi-plus-square"></span>',
                               css_class='btn btn-sm btn-primary',
                               **btn_add_attrs)

        return btn_add

    def get_list_container(self, prefix, _list):
        btn_add = self.get_list_add_btn(prefix)
        select_field = FieldWithButtons(
            Field(f'{prefix}_select', css_class='form-select-sm'),
            btn_add,
            css_class='input-group-sm'
        )
        component = Div(
            select_field,
            Row(
                Field(prefix, wrapper_class="d-none"),
                HTML(_list),
                id=f'div_id_{prefix}',
            ),
            css_class='card card-body border border-dark mb-2'
        )
        return component

    def init_contact_list(self, prefix, group):
        _list = ""
        contacts = []
        if self.instance.pk:
            contact_list = getattr(self.instance, prefix)
            contacts = [con.id for con in contact_list.all()] if self.instance.pk else []

        if not contacts:
            if self.data and f'{prefix}_bullet' in self.data:
                contacts = self.data.getlist(f'{prefix}_bullet')

        if contacts:
            for contact_id in contacts:
                _list += get_contact_bullet(contact_id, User, prefix, 'core:remove_from_list')

        # Filter chief scientists to only include contacts with the "chief scientist" role
        _group = Group.objects.filter(name__iexact=group).first()
        if _group:
            users = User.objects.filter(groups=_group).order_by('last_name', 'first_name')
            self.fields[f'{prefix}_select'].queryset = users
            self.fields[f'{prefix}_select'].label_from_instance = lambda user: f'{user.last_name}, {user.first_name}'

            self.fields[prefix].queryset = users

        return self.get_list_container(prefix, _list)

    def init_lookup(self, prefix, model):
        _list = ""
        lookups = []

        if self.instance.pk:
            lookup_list = getattr(self.instance, prefix)
            lookups = [lu.id for lu in lookup_list.all()] if self.instance.pk else []

        if not lookups:
            if self.data and f'{prefix}_bullet' in self.data:
                lookups = self.data.getlist(f'{prefix}_bullet')

        for lu_id in lookups:
            _list += get_lookup_bullet(lu_id, model, prefix, 'core:remove_from_list')

        self.fields[f'{prefix}_select'].queryset = model.objects.all()
        self.fields[prefix].queryset = model.objects.all()

        return self.get_list_container(prefix, _list)


    def __init__(self, *args, **kwargs):
        super(CruiseForm, self).__init__(*args, **kwargs)

        scientists_container = self.init_contact_list('chief_scientists', 'chief scientists')
        data_manager_container = self.init_contact_list('data_managers', 'data managers')
        locations_container = self.init_lookup('locations', models.GeographicRegions)
        programs_container = self.init_lookup('programs', models.Programs)

        submit_url = (reverse_lazy('core:update_cruise', args=[self.instance.pk])
                      if self.instance.pk else
                      reverse_lazy('core:add_cruise'))
        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_id_cruise",
            'hx-post': submit_url
        }

        btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{_("Save Updates")}',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_submit_attrs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
        Row(
                    Column(Field('name'), css_class='form-control-sm'),
                    Column(Field('descriptor', placeholder=_("optional, if known")), css_class='form-control-sm'),
                    Column(Field('platform'), css_class='form-select-sm'),
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            ),
            Div(
                Row(
                Column(Field('start_date'), css_class='col-auto form-control-sm'),
                    Column(Field('end_date'), css_class='col-auto form-control-sm'),
                ),
                css_class="card card-body mb-2 border border-dark"
            ),
            Row(
                Column(scientists_container),
                Column(data_manager_container),
            ),
            Row(
                Column(programs_container),
                Column(locations_container),
            ),
            btn_submit
        )


@login_required
def update_cruise(request, **kwargs):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))

    # Create a mutable copy of the POST data
    post_data = request.POST.copy()

    # If locations_select has a value but locations is empty, add the selection to locations
    if 'locations_select' in post_data and post_data.get('locations_select') and not post_data.getlist('locations'):
        location_id = post_data.get('locations_select')
        post_data.setlist('locations', [location_id])

    # If locations_select has a value but locations is empty, add the selection to locations
    if 'chief_scientists_select' in post_data and post_data.get('chief_scientists_select') and not post_data.getlist('chief_scientists'):
        location_id = post_data.get('chief_scientists_select')
        post_data.setlist('chief_scientists', [location_id])

    if 'cruise_id' in kwargs:
        cruise_id = int(kwargs.get('cruise_id'))
        cruise = models.Cruises.objects.get(pk=cruise_id)
        form = CruiseForm(post_data, instance=cruise)
    else:
        form = CruiseForm(post_data)

    if form.is_valid():
        try:
            cruise = form.save()
            response = HttpResponse()
            response['HX-Redirect'] = reverse_lazy('core:update_cruise_view', args=[cruise.id])
            return response
        except Exception as ex:
            logger.error("Failed to save the cruise form.")
            logger.exception(ex)
            form.add_error(None, _("An unexpected error occurred while saving the form."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


def get_contact_bullet(contact_id, lookup_model, prefix, post_remove_url_alias):
    contact = lookup_model.objects.get(pk=contact_id)

    context = {
        'input_name': f'{prefix}_bullet',
        'value_id': contact.pk,
        'value_label': f"{contact.last_name}, {contact.first_name}",
        'post_url': reverse_lazy(post_remove_url_alias, args=[prefix, contact.pk]),
    }
    return render_to_string('core/partial/multi_select_bullet.html', context=context)


def get_lookup_bullet(id, lookup_model, prefix, post_remove_url_alias):
    lookup_obj = lookup_model.objects.get(pk=id)

    context = {
        'input_name': f'{prefix}_bullet',
        'value_id': lookup_obj.pk,
        'value_label': f"{lookup_obj.name}",
        'post_url': reverse_lazy(post_remove_url_alias, args=[prefix, lookup_obj.pk]),
    }
    return render_to_string('core/partial/multi_select_bullet.html', context=context)


def get_updated_list(contact_ids: [int], prefix):
    form = CruiseForm(initial={prefix: contact_ids})
    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    form_select = form_soup.find(id=f"id_{prefix}")
    form_select.attrs['hx-swap'] = 'outerHTML'
    form_select.attrs['hx-swap-oob'] = 'true'

    return form_select


def add_to_list(request, prefix):
    new_id = request.POST.get(f'{prefix}_select')

    existing = request.POST.getlist(f'{prefix}_bullet')
    if new_id in existing:
        return HttpResponse()

    soup = BeautifulSoup()

    get_bullet_func = get_contact_bullet
    lookup_model = User
    if prefix == 'locations':
        get_bullet_func = get_lookup_bullet
        lookup_model = models.GeographicRegions
    elif prefix == 'programs':
        get_bullet_func = get_lookup_bullet
        lookup_model = models.Programs

    new_pill = get_bullet_func(new_id, lookup_model, prefix, 'core:remove_from_list')

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    existing_ids.append(int(new_id))

    soup.append(get_updated_list(existing_ids, prefix))
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return HttpResponse(soup)


def remove_from_list(request, contact_id, prefix):
    existing_ids = [int(id) for id in request.POST.getlist(prefix)]
    if contact_id not in existing_ids:
        return HttpResponse()

    soup = BeautifulSoup()

    existing_ids.remove(contact_id)
    soup.append(get_updated_list(existing_ids, prefix))

    return HttpResponse(soup)


urlpatterns = [
    path('cruise/new', CreateCruise.as_view(), name='new_cruise_view'),
    path('cruise/<int:cruise_id>', CreateCruise.as_view(), name='update_cruise_view'),
    path('cruise/add-cruise', update_cruise, name='add_cruise'),
    path('cruise/update/<int:cruise_id>', update_cruise, name='update_cruise'),

    path('cruise/add/<str:prefix>', add_to_list, name='add_to_list'),
    path('cruise/remove/<str:prefix>/<int:contact_id>', remove_from_list, name='remove_from_list'),
]
