from bs4 import BeautifulSoup

from django.urls import path, reverse_lazy
from django.template.loader import render_to_string
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Hidden, Row, Column, Field, Div, HTML, Submit
from crispy_forms.bootstrap import StrictButton
from crispy_forms.utils import render_crispy_form

from core import models


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
            raise forms.ValidationError(_("At least one chief scientist must be selected."))

        # Additional processing or validation logic can go here

        return chief_scientists

    def __init__(self, *args, **kwargs):

        super(CruiseForm, self).__init__(*args, **kwargs)

        scientists = None
        scientists_list = ""
        if self.data and 'chief_scientists_bullet' in self.data:
            scientists = self.data.getlist('chief_scientists_bullet')
            for scientist_id in scientists:
                scientists_list += get_scientists_bullet(scientist_id)

        # Filter chief scientists to only include contacts with the "chief scientists" role
        chief_scientist_role = models.ContactRoles.objects.filter(name__iexact='chief scientist').first()
        if chief_scientist_role:
            self.fields['chief_scientists_select'].queryset = models.Contacts.objects.filter(roles=chief_scientist_role)
            self.fields['chief_scientists'].queryset = models.Contacts.objects.filter(roles=chief_scientist_role)

        btn_add_attrs = {
            'hx-target': "#div_id_cheif_scientists",
            'hx-post': reverse_lazy('core:add_chief_scientist'),
            'hx-swap': "beforeend"
        }

        btn_add_scientist = StrictButton('<span class="bi bi-plus-square"></span>',
                                         css_class='btn btn-sm btn-primary mb-1',
                                         **btn_add_attrs)

        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_id_cruise",
            'hx-post': reverse_lazy('core:add_cruise'),
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
                Column(Field('locations'), css_class='form-control-sm'),
            ),
            btn_submit
        )


class CreateCruise(TemplateView):
    template_name = 'core/form_cruise.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['title'] = _('Create Cruise')
        context['cruise_form'] = CruiseForm()

        return context


def get_scientists_bullet(contact_id):
    scientist = models.Contacts.objects.get(pk=contact_id)

    context = {
        'input_name': 'chief_scientists_bullet',
        'value_id': scientist.pk,
        'value_label': str(scientist),
        'post_url': reverse_lazy('core:add_chief_scientist'),
    }

    new_pill = render_to_string('core/partial/multi_select_bullet.html', context=context)
    return new_pill



def add_chief_scientist(request):
    new_scientist_id = request.POST.get('chief_scientists_select')

    existing = request.POST.getlist('chief_scientists_bullet')
    if new_scientist_id in existing:
        return HttpResponse()

    soup = BeautifulSoup()

    new_pill = get_scientists_bullet(new_scientist_id)

    existing_ids = [int(pk) for pk in existing if pk.isdigit()]
    form = CruiseForm(initial={'chief_scientists': existing_ids})
    crispy = render_crispy_form(form)
    form_soup = BeautifulSoup(crispy, 'html.parser')
    scientist_select = form_soup.find(id="id_chief_scientists")
    scientist_select.attrs['hx-swap'] = 'outerHTML'
    scientist_select.attrs['hx-swap-oob'] = 'true'

    soup.append(scientist_select)
    soup.append(BeautifulSoup(new_pill, 'html.parser'))

    return HttpResponse(soup)


def remove_chief_scientist(request):
    return HttpResponse('')


def add_cruise(request):
    form = CruiseForm(request.POST)

    if form.is_valid():
        form.save()
        crispy = render_crispy_form(form)
        return HttpResponse(crispy)

    crispy = render_crispy_form(form)
    soup = BeautifulSoup(crispy, 'html.parser')
    return HttpResponse(soup)


urlpatterns = [
    path('curise/new', CreateCruise.as_view(), name='new_cruise'),
    path('cruise/add-cruise', add_cruise, name='add_cruise'),
    path('cruise/add-chief-scientist', add_chief_scientist, name='add_chief_scientist'),
    path('cruise/add-chief-scientist', add_chief_scientist, name='remove_chief_scientist'),
]
