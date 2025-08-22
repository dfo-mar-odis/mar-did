from django.urls.conf import path
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView


class LandingView(TemplateView):
    template_name = "core/view_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['links'] = [
            {
                'title': _('Work Queue'),
                'url': '',
                'icon': 'bi-journal-text'
            },
            {
                'title': _('Add a Cruise'),
                'url': reverse('core:cruise_view'),
                'icon': 'bi-life-preserver'
            },
            {
                'title': _('Data Discovery'),
                'url': '',
                'icon': 'bi-search'
            },
        ]

        return context

urlpatterns = [
  path('', LandingView.as_view(), name='landing_view'),
]