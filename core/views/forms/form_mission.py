from bs4 import BeautifulSoup

from django import forms
from django.urls import path, reverse_lazy
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic.base import TemplateView
from django.contrib.auth.models import User, Group
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field, HTML, Hidden
from crispy_forms.bootstrap import StrictButton, FieldWithButtons
from crispy_forms.utils import render_crispy_form

from core import models

import logging

from core.views.view_data import ExpectedDataForm

logger = logging.getLogger('mardid')

# Registered functions for controlling multi-select UI components.
BULLET_LIST_FUNCTION_REGISTER = {
    'regions': {
        # specify what function is used to manage the bullet list, get_list_bullet is generic
        # and will work in most common cases, but a custom function can be supplied
        'bullet_function': 'get_list_bullet',

        # lookup model that's to be used to populate dropdowns
        'lookup_model': models.GeographicRegions,

        # Function to render an element, this allows control over what parts and how an element is displayed
        # could be something like: f'{element.last_name}, {element.first_name} - {element.phone_number}'
        'render_function': lambda element: f"{element}",

        # url to call when adding an element to the list
        'add_url': 'core:add_to_list',

        # url to call when removing an element from the list
        'remove_url': 'core:remove_from_list'
    }
}

class CreateMission(LoginRequiredMixin, TemplateView):
    template_name = 'core/form_mission.html'
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.groups.filter(name__in=['Chief Scientists', 'MarDID Maintainers']).exists():
            return redirect(reverse_lazy('login'))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Create Mission')
        if 'mission_id' in self.kwargs:
            context['object'] = models.Missions.objects.get(pk=self.kwargs['mission_id'])
            context['mission_form'] = MissionForm(instance=context['object'])
            context['mission_leg_form'] = MissionLegForm(context['object'], initial={'mission': context['object']})
        else:
            context['mission_form'] = MissionForm()

        return context


class MissionLegForm(forms.ModelForm):
    regions_select = forms.ModelChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        label=_("Select Geographic Locations"),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    regions = forms.ModelMultipleChoiceField(
        queryset=models.GeographicRegions.objects.none(),
        label=_("Geographic Locations")
    )

    class Meta:
        model = models.Legs
        fields = '__all__'

        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'max': '9999-12-31'}),
        }

    def clean_regions_field(self):
        regions_select = self.data.get('regions_select')
        regions = self.data.getlist('regions_bullet')

        keys = [int(location) for location in regions]
        if regions_select:
            keys.append(int(regions_select))

        cleaned_regions = models.GeographicRegions.objects.filter(pk__in=keys)

        # Example validation: Ensure at least one chief scientist is selected
        if not cleaned_regions.exists():
            self.add_error('regions_select', _("At least one geographic location must be added."))  # Non-field error
            self.fields['regions_select'].widget.attrs.update({'class': 'is-invalid'})  # Highlight field

        # Additional processing or validation logic can go here

        return cleaned_regions

    def clean_regions_select(self):
        return self.clean_regions_field()

    def get_list_add_btn(self, prefix):
        registered_multi_select = BULLET_LIST_FUNCTION_REGISTER.get(prefix, None)
        if registered_multi_select is None:
            raise Exception(f"No bullet function registered for prefix {prefix}")

        btn_add_attrs = {
            'hx-target': f"#div_id_{prefix}",
            'hx-post': reverse_lazy(registered_multi_select['add_url'], args=[prefix]),
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

    def init_lookup(self, prefix):
        _list = ""
        lookups = []

        register_multi_select = BULLET_LIST_FUNCTION_REGISTER.get(prefix, None)
        if register_multi_select is None:
            raise Exception(f"No bullet function registered for prefix {prefix}")

        model = register_multi_select['lookup_model']
        if self.instance.pk:
            lookup_list = getattr(self.instance, prefix)
            lookups = [lu.id for lu in lookup_list.all()] if self.instance.pk else []

        if not lookups:
            if self.data and f'{prefix}_bullet' in self.data:
                lookups = self.data.getlist(f'{prefix}_bullet')

        for lu_id in lookups:
            _list += get_list_bullet(lu_id, prefix)

        self.fields[f'{prefix}_select'].queryset = model.objects.all()
        self.fields[prefix].queryset = model.objects.all()

        return self.get_list_container(prefix, _list)

    # if mission is none this will return a form with no submit buttons. It's only intended to get updated UI elements
    def __init__(self, mission: models.Missions|None, *args, **kwargs):
        mission_id = mission.pk if mission is not None else -1
        if mission is not None and 'instance' not in kwargs:
            leg_number = mission.legs.order_by('-number').first().number + 1 if mission.legs.exists() else 1
            initial = kwargs.pop('initial') if 'initial' in kwargs else {}
            initial['number'] = leg_number

            super(MissionLegForm, self).__init__(initial=initial, *args, **kwargs)
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

            btn_submit_attrs = {
                'title': _("Submit"),
                'hx-target': "#form_id_mission_leg",
                'hx-post': submit_url
            }

            btn_label = _("Save Leg")
            btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{btn_label}',
                                      css_class='btn btn-sm btn-primary mb-1',
                                      **btn_submit_attrs)

            self.helper.layout.fields[0].fields.append(Div(btn_submit))

    def save(self, commit=True):
        leg = super(MissionLegForm, self).save(commit=False)

        if commit:
            leg.save()

            regions = self.clean_regions_field()
            leg.regions.set(regions)

        return leg

class MissionForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super(MissionForm, self).__init__(*args, **kwargs)

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
                Div(
                    btn_submit
                ),
                css_class="card card-body mb-2 border border-dark bg-light"
            ),

        )


@login_required
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
            response['HX-Redirect'] = reverse_lazy('core:update_mission_view', args=[mission.id])
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


def get_list_bullet(element_id, prefix):
    registered_multi_select = BULLET_LIST_FUNCTION_REGISTER[prefix]
    element = registered_multi_select['lookup_model'].objects.get(pk=element_id)

    context = {
        'input_name': f'{prefix}_bullet',
        'value_id': element.pk,
        'value_label': registered_multi_select['render_function'](element),
        'post_url': reverse_lazy(registered_multi_select['remove_url'], args=[prefix, element.pk]),
    }
    return render_to_string('core/partials/components/multi_select_bullet.html', context=context)


def get_updated_list(element_ids: list[int], prefix):
    form = MissionLegForm(mission=None, initial={prefix: element_ids})
    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    form_select = form_soup.find(id=f"id_{prefix}")
    form_select.attrs['hx-swap'] = 'outerHTML'
    form_select.attrs['hx-swap-oob'] = 'true'

    return form_select

def add_to_list(request, prefix):

    registered_multi_select = BULLET_LIST_FUNCTION_REGISTER.get(prefix, None)
    if registered_multi_select is None:
        raise Exception(f"No bullet function registered for prefix {prefix}")

    new_id = request.POST.get(f'{prefix}_select')

    existing = request.POST.getlist(f'{prefix}_bullet')
    if new_id in existing:
        return HttpResponse()

    soup = BeautifulSoup()

    get_bullet_func = globals()[registered_multi_select['bullet_function']]
    new_pill = get_bullet_func(new_id, prefix)

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    existing_ids.append(int(new_id))

    soup.append(get_updated_list(existing_ids, prefix))
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return HttpResponse(soup)


def remove_from_list(request, element_id: int, prefix):
    existing_ids = [int(id) for id in request.POST.getlist(prefix)]
    if element_id not in existing_ids:
        return HttpResponse()

    soup = BeautifulSoup()

    existing_ids.remove(element_id)
    soup.append(get_updated_list(existing_ids, prefix))

    return HttpResponse(soup)


def mission_leg_list(request, mission_id):
    mission = models.Missions.objects.get(pk=mission_id)

    context = {
        'mission': mission
    }
    html = render_to_string('core/partials/table_mission_legs.html', context=context)
    return HttpResponse(html)


def mission_leg_form(request, mission_id, **kwargs):
    mission = models.Missions.objects.get(pk=mission_id)

    if 'leg_id' in kwargs:
        leg_id = int(kwargs.get('leg_id'))
        leg = models.Legs.objects.get(pk=leg_id)
        form = MissionLegForm(mission, instance=leg)
    else:
        form = MissionLegForm(mission)

    html = render_crispy_form(form)
    return HttpResponse(html)


def mission_leg_delete(request, mission_id, leg_id):
    leg = models.Legs.objects.get(pk=leg_id)
    leg.delete()

    return HttpResponse()


urlpatterns = [
    path('mission/new', CreateMission.as_view(), name='new_mission_view'),
    path('mission/<int:mission_id>', CreateMission.as_view(), name='update_mission_view'),
    path('mission/add-mission', update_mission, name='add_mission'),
    path('mission/update/<int:mission_id>', update_mission, name='update_mission'),

    path('mission/add/<str:prefix>', add_to_list, name='add_to_list'),
    path('mission/remove/<str:prefix>/<int:element_id>', remove_from_list, name='remove_from_list'),

    path('mission/leg/new/<int:mission_id>/<int:leg_id>', mission_leg_form, name='mission_leg_form'),
    path('mission/leg/list/<int:mission_id>', mission_leg_list, name='mission_leg_list'),
    path('mission/leg/add-mission/<int:mission_id>', mission_leg_update, name='add_mission_leg'),
    path('mission/leg/update/<int:mission_id>/<int:leg_id>', mission_leg_update, name='update_mission_leg'),
    path('mission/leg/add-mission/<int:mission_id>/<int:leg_id>', mission_leg_delete, name='mission_leg_delete'),
]
