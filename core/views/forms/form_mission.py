from bs4 import BeautifulSoup

from django import forms
from django.urls import path, reverse_lazy, reverse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field, Hidden
from crispy_forms.bootstrap import StrictButton
from crispy_forms.utils import render_crispy_form

from core import models

import logging

from core.views.forms import form_multiselect

logger = logging.getLogger('mardid')

class CreateMission(LoginRequiredMixin, TemplateView):
    template_name = 'core/forms/form_mission.html'
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name__in=['Chief Scientists', 'MarDID Maintainers']).exists():
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Create Mission')
        if 'mission_id' in self.kwargs:
            context['object'] = models.Missions.objects.get(pk=self.kwargs['mission_id'])
            context['mission_form'] = MissionForm(instance=context['object'])
            context['mission_legs_form'] = MissionLegForm(context['object'], initial={'mission': context['object']})
        else:
            context['mission_form'] = MissionForm()

        return context


class MissionLegForm(form_multiselect.MultiselectFieldForm):
    chief_scientist = forms.ModelChoiceField(
        queryset=models.Participants.objects.all(),
        label=_("Chief Scientist"),
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )

    regions_select = forms.ModelChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        label=_("Select Geographic Locations*"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    regions = forms.ModelMultipleChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        required=False,
        label=_("Geographic Locations")
    )

    class Meta:
        model = models.Legs
        fields = '__all__'

        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
        }

    def get_multiselect_context(self, prefix) -> form_multiselect.MultiselectContext | None:
        return MULTISELECT_CONTEXT_REGISTER.get(prefix, None)

    def clean_regions_select(self):
        return self.clean_multiselect_field('regions', models.GeographicRegions)

    def clean_regions(self):
        prefix = 'regions'
        cleaned_regions = self.clean_multiselect_field(prefix, models.GeographicRegions)
        if not cleaned_regions:
            self.add_error(f'{prefix}_select', _("At least one geographic region must be added."))  # Non-field error
            self.fields[f'{prefix}_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        return cleaned_regions

    # if mission is none this will return a form with no submit buttons. It's only intended to get updated UI elements
    def __init__(self, mission: models.Missions | None = None, *args, **kwargs):
        mission_id = mission.pk if mission is not None else -1
        if mission is not None and 'instance' not in kwargs:
            leg_number = mission.legs.order_by('-number').first().number + 1 if mission.legs.exists() else 1
            initial = kwargs.pop('initial') if 'initial' in kwargs else {}
            initial['number'] = leg_number

            super(MissionLegForm, self).__init__(initial=initial, *args, **kwargs)
        elif 'instance' in kwargs:
            leg = kwargs['instance']
            chief_scientist = leg.leg_participants.filter(position__name="Chief Scientist")
            if chief_scientist.exists():
                chief_scientist = chief_scientist.first()
                initial = kwargs.pop('initial') if 'initial' in kwargs else {}
                initial['chief_scientist'] = chief_scientist.participant.pk

                super(MissionLegForm, self).__init__(initial=initial, *args, **kwargs)
            else:
                super(MissionLegForm, self).__init__(*args, **kwargs)
        else:
            super(MissionLegForm, self).__init__(*args, **kwargs)

        regions_container = self.init_lookup('regions')

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                Hidden('mission', mission_id),
                Row(
                    Column(Field('number'), css_class='form-control-sm'),
                    Column(Field('start_date'), css_class='form-control-sm'),
                    Column(Field('end_date'), css_class='form-control-sm'),
                    Column(Field('description'), css_class='form-control-sm'),
                ),
                Row(
                    Column(Field('chief_scientist'), css_class='form-select-sm'),
                ),
                Row(
                    Column(regions_container),
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            ),
        )

        if mission_id > 0:
            # if an instant is present then we're going to use the 'update_mission' url, otherwise we'll use the url
            # to create a new mission
            if self.instance.pk:
                submit_url = reverse_lazy('core:update_mission_leg', args=[mission_id, self.instance.pk])
            else:
                submit_url = reverse_lazy('core:add_mission_leg', args=[mission_id])

            button_div = Div()
            btn_submit_attrs = {
                'title': _("Submit"),
                'hx-target': "#form_id_mission_leg",
                'hx-post': submit_url
            }

            btn_label = _("Save Leg")
            btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label}',
                                      css_class='btn btn-sm btn-primary mb-1',
                                      **btn_submit_attrs)
            button_div.append(btn_submit)

            btn_new_leg_attrs = {
                'hx-target': "#form_id_mission_leg",
                'hx-get': reverse_lazy('core:mission_leg_form_clear', args=[mission_id]),
            }
            btn_label_new = _("New Leg")
            btn_new = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label_new}',
                                   css_class='btn btn-sm btn-secondary mb-1',
                                   **btn_new_leg_attrs)
            button_div.append(btn_new)
            self.helper.layout.fields[0].fields.append(button_div)

    def save(self, commit=True):
        leg = super(MissionLegForm, self).save(commit=False)

        if commit:
            leg.save()

            regions = self.cleaned_data['regions']
            leg.regions.set(regions)

            # Handle the chief scientist
            chief_scientist = self.cleaned_data.get('chief_scientist')
            if chief_scientist:
                position = models.Positions.objects.get(name="Chief Scientist")

                # Remove any existing chief scientist for this leg
                models.MissionParticipants.objects.filter(leg=leg, position=position).delete()

                # Add the new chief scientist for this leg
                models.MissionParticipants.objects.update_or_create(
                    leg=leg,
                    position=position,
                    defaults={'participant': chief_scientist}
                )

        return leg


class MissionForm(form_multiselect.MultiselectFieldForm):
    organizations_select = forms.ModelChoiceField(
        queryset=models.Organizations.objects.none(),
        label=_("Select Organizations"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    organizations = forms.ModelMultipleChoiceField(
        queryset=models.Organizations.objects.none(),
        required=False,
        label=_("Organizations")
    )

    class Meta:
        model = models.Missions
        fields = '__all__'

        ##########################################################################################
        # This is specifically so labels and help text are translated
        ##########################################################################################
        labels = {
        }

        help_texts = {
        }
        ##########################################################################################

        # widgets = {
        #     'start_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
        #     'end_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
        # }

    def get_multiselect_context(self, prefix) -> form_multiselect.MultiselectContext | None:
        return MULTISELECT_CONTEXT_REGISTER.get(prefix, None)

    def clean_organizations_select(self):
        return self.clean_multiselect_field('organizations', models.Organizations)

    def clean_organizations(self):
        prefix = 'organizations'
        cleaned_regions = self.clean_multiselect_field(prefix, models.Organizations)

        return cleaned_regions

    def __init__(self, *args, **kwargs):
        super(MissionForm, self).__init__(*args, **kwargs)

        organizations_container = self.init_lookup('organizations')

        # if an instant is present then we're going to use the 'update_mission' url, otherwise we'll use the url
        # to create a new mission
        if self.instance.pk:
            submit_url = reverse_lazy('core:update_mission', args=[self.instance.pk])
        else:
            submit_url = reverse_lazy('core:add_mission')

        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_id_mission",
            'hx-post': submit_url
        }

        btn_label = _("Save Updates")
        btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label}',
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
                    Column(Field('program'), css_class='form-select-sm'),
                ),
                Row(
                    Column(organizations_container),
                ),
                Div(
                    btn_submit
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            ),

        )

    def save(self, commit=True):
        mission = super(MissionForm, self).save(commit=False)

        if commit:
            mission.save()

            organizations = self.cleaned_data['organizations']
            if organizations:
                mission.organizations.set(organizations)
            else:
                mission.organizations.clear()

        return mission


def update_mission(request, **kwargs):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))

    # Review code in core.views.forms.form_mission_reference.update_mission for an example of how
    # to handle the select and multi-select fields together in this view

    # Create a mutable copy of the POST data
    post_data = request.POST.copy()

    if 'mission_id' in kwargs:
        mission_id = int(kwargs.get('mission_id'))
        mission = models.Missions.objects.get(pk=mission_id)
        form = MissionForm(post_data, instance=mission)
    else:
        form = MissionForm(post_data)

    if form.is_valid():
        try:
            mission = form.save()
            response = HttpResponse()
            response['HX-Redirect'] = reverse('core:update_mission_view', args=[mission.id])
            return response
        except Exception as ex:
            logger.error("Failed to save the mission form.")
            logger.exception(ex)
            form.add_error(None, _("An unexpected error occurred while saving the form."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


@login_required
def mission_leg_update(request, mission_id, **kwargs):
    if not request.user.is_authenticated:
        return redirect(reverse_lazy('login'))

    # Review code in core.views.forms.form_mission_reference.update_mission for an example of how
    # to handle the select and multi-select fields together in this view

    # Create a mutable copy of the POST data
    post_data = request.POST.copy()

    mission = models.Missions.objects.get(pk=mission_id)
    if 'leg_id' in kwargs:
        leg_id = int(kwargs.get('leg_id'))
        mission_leg = models.Legs.objects.get(pk=leg_id)
        form = MissionLegForm(mission, post_data, instance=mission_leg)
    else:
        form = MissionLegForm(mission, post_data)

    if form.is_valid():
        try:
            leg = form.save()
            form = MissionLegForm(mission, instance=leg)
            crispy = render_crispy_form(form)
            soup = BeautifulSoup(crispy, 'html.parser')

            response = HttpResponse(soup)
            response['HX-Trigger'] = 'mission_leg_updated'
            return response
        except Exception as ex:
            logger.error("Failed to save the mission leg form.")
            logger.exception(ex)
            form.add_error(None, _("An unexpected error occurred while saving the form."))
            crispy = render_crispy_form(form)
            return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


def mission_leg_list(request, mission_id):
    mission = models.Missions.objects.get(pk=mission_id)

    context = {
        'mission': mission
    }
    html = render_to_string('core/partials/table_mission_legs.html', context=context)
    return HttpResponse(html)


def mission_leg_form(request, mission_id, **kwargs):
    if 'leg_id' in kwargs:
        leg_id = int(kwargs.get('leg_id'))
        leg = models.Legs.objects.get(pk=leg_id)
        mission = leg.mission
        form = MissionLegForm(mission, instance=leg)
    else:
        mission = models.Missions.objects.get(pk=mission_id)
        form = MissionLegForm(mission)

    html = render_crispy_form(form)
    return HttpResponse(html)


def mission_leg_delete(request, mission_id, leg_id):
    leg = models.Legs.objects.get(pk=leg_id)
    leg.delete()

    return HttpResponse()


# Registered functions for controlling multi-select UI components.
MULTISELECT_CONTEXT_REGISTER = {
    'regions': form_multiselect.MultiselectContext(
        prefix='regions',
        lookup_model=models.GeographicRegions,
        form_class=MissionLegForm,
        render_function=lambda element: f"{element.name}",
        add_url='core:add_to_list',
        remove_url='core:remove_from_list'
    ),
    'organizations': form_multiselect.MultiselectContext(
        prefix='organizations',
        lookup_model=models.Organizations,
        form_class=MissionForm,
        render_function=lambda element: f"{element.acronym}",
        add_url='core:add_to_list',
        remove_url='core:remove_from_list'
    ),
}

def add_to_list(request, prefix):
    multiselect_context = MULTISELECT_CONTEXT_REGISTER.get(prefix, None)
    if not multiselect_context:
        return HttpResponse(status=400)

    if soup := form_multiselect.add_to_list(request, multiselect_context, prefix):
        return HttpResponse(soup)

    return HttpResponse()


def remove_from_list(request, prefix, element_id):
    multiselect_context = MULTISELECT_CONTEXT_REGISTER.get(prefix, None)
    if not multiselect_context:
        return HttpResponse(status=400)

    if soup := form_multiselect.remove_from_list(request,multiselect_context, element_id):
        return HttpResponse(soup)

    return HttpResponse()


def get_updated_list(request, prefix):
    multiselect_context = MULTISELECT_CONTEXT_REGISTER.get(prefix, None)
    if not multiselect_context:
        return HttpResponse(status=400)

    if soup := form_multiselect.get_updated_list(request, multiselect_context):
        return HttpResponse(soup)

    return HttpResponse()


urlpatterns = [
    path('mission/new', CreateMission.as_view(), name='new_mission_view'),
    path('mission/<int:mission_id>', CreateMission.as_view(), name='update_mission_view'),
    path('mission/add-mission', update_mission, name='add_mission'),
    path('mission/update/<int:mission_id>', update_mission, name='update_mission'),

    path('mission/add/<str:prefix>', add_to_list, name='add_to_list'),
    path('mission/remove/<str:prefix>/<int:element_id>', remove_from_list, name='remove_from_list'),

    path('mission/leg/new/<int:mission_id>/', mission_leg_form, name='mission_leg_form_clear'),
    path('mission/leg/new/<int:mission_id>/<int:leg_id>', mission_leg_form, name='mission_leg_form'),
    path('mission/leg/list/<int:mission_id>', mission_leg_list, name='mission_leg_list'),
    path('mission/leg/add-mission/<int:mission_id>', mission_leg_update, name='add_mission_leg'),
    path('mission/leg/update/<int:mission_id>/<int:leg_id>', mission_leg_update, name='update_mission_leg'),
    path('mission/leg/add-mission/<int:mission_id>/<int:leg_id>', mission_leg_delete, name='mission_leg_delete'),
]
