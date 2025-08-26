from bs4 import BeautifulSoup

from http.client import HTTPResponse

from crispy_forms.utils import render_crispy_form
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Row, Column, Field, HTML
from crispy_forms.bootstrap import StrictButton

from django import forms
from django.http import HttpResponse
from django.urls import path, reverse_lazy
from django.utils.translation import gettext as _
from django.template.loader import render_to_string
from django.contrib.auth.models import User, Group
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class ContactView(TemplateView):
    template_name = 'core/view_contacts_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Contacts List'
        context['container'] = 'container-fluid'
        context['contacts'] = User.objects.all().order_by('last_name', 'first_name')
        return context


class ContactForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'groups']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_tag = False

        btn_clear_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_contacts_form_area",
            'hx-post': reverse_lazy('core:get_contact_form')
        }

        btn_clear = StrictButton(f'<span class="bi bi-eraser me-2"></span>{_("Clear Form")}',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_clear_attrs)

        submit_url = (reverse_lazy('core:update_contact', args=[self.instance.pk])
                      if self.instance.pk else
                      reverse_lazy('core:add_contact'))

        btn_submit_attrs = {
            'title': _("Submit"),
            'hx-target': "#form_contacts_form_area",
            'hx-post': submit_url
        }

        btn_submit = StrictButton(f'<span class="bi bi-check-square me-2"></span>{_("Save Updates")}',
                                  css_class='btn btn-sm btn-primary mb-1',
                                  **btn_submit_attrs)

        message = _("Note, this interface allows users to be added so they can be used in the interface, but they will not receive passwords and cannot login. Contact the adminastrator to have passwords assigned.")
        alert = HTML(f'<div class="alert alert-info">{message}</div>')
        self.helper.layout = Layout(
            Div(alert),
            Div(
                Div(
                    Row(
                        Column(Field('username')),
                        Column(Field('first_name')),
                        Column(Field('last_name')),
                        Column(Field('email')),
                    ),
                    Row(
                        Column(Field('groups'))
                    ),
                    Row(
                        Column(btn_submit if btn_submit else None, css_class='col-auto'),
                        Column(btn_clear if btn_clear else None, css_class='col-auto'),
                    ),
                    css_class="card-body"
                ),
                css_class = "card mb-2"
            )
        )

def authenticated(request):
    # Check if user belongs to MarDID Maintainers or Chief Scientists groups
    if request.user.groups.filter(name__in=['Chief Scientists', 'MarDID Maintainers']).exists():
        return True

    return False


def list_contacts(request):
    context = {
        'contacts': User.objects.all().order_by('last_name', 'first_name'),
        'user': request.user
    }
    html = render_to_string('core/partial/table_contacts_list.html', context=context)
    soup = BeautifulSoup(html, 'html.parser')

    return HttpResponse(soup.find('table', id="table_id_contacts_list"))

def get_contact_form(request, **kwargs):
    if not authenticated(request):
        next_page = reverse_lazy('core:contacts_view')
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return response

    if 'contact_id' in kwargs:
        contact = User.objects.get(pk=kwargs['contact_id'])
        form = ContactForm(instance=contact)
    else:
        form = ContactForm()

    html = render_crispy_form(form)

    return HttpResponse(html)


def update_contact(request, **kwargs):
    if not authenticated(request):
        next_page = request.path
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return HttpResponse(response)

    if 'contact_id' in kwargs:
        contact = User.objects.get(pk=kwargs['contact_id'])
        form = ContactForm(request.POST, instance=contact)
    else:
        form = ContactForm(request.POST)

    if form.is_valid():
        form.save()
        response = HttpResponse(render_crispy_form(ContactForm()))
        response['HX-Trigger'] = 'update_list'
        return response

    html = render_crispy_form(form)
    return HttpResponse(html)


def remove_contact(request, contact_id):
    if not authenticated(request):
        next_page = request.path
        login_url = f"{reverse_lazy('login')}?next={next_page}"
        response = HttpResponse()
        response['HX-Redirect'] = login_url
        return HttpResponse(response)

    user = User.objects.get(pk=contact_id)
    user.delete()

    return HttpResponse()


urlpatterns = [
    path('contacts', ContactView.as_view(), name='contacts_view'),
    path('contacts/form', get_contact_form, name='get_contact_form'),
    path('contacts/form/<int:contact_id>', get_contact_form, name='get_contact_form'),
    path('contacts/list', list_contacts, name='list_contacts'),
    path('contacts/add', update_contact, name='add_contact'),
    path('contacts/update/<int:contact_id>', update_contact, name='update_contact'),
    path('contacts/remove/<int:contact_id>', remove_contact, name='remove_contact'),
]