from django.urls.conf import path
from django.urls import reverse
from django.utils.translation import gettext as _
from django.views.generic.base import TemplateView

from core import models

class LandingView(TemplateView):
    template_name = "core/view_landing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        datastatus = models.DataStatus.objects.get(name__iexact="Submitted")
        context['dataset_submitted'] = models.Dataset.objects.filter(status=datastatus).count()

        context['dataset_assigned'] = models.Processing.objects.all().count()
        return context

urlpatterns = [
  path('', LandingView.as_view(), name='landing_view'),
]