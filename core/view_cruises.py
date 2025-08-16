from django.urls import path
from django.views.generic.base import TemplateView
from .forms import form_cruise

class LandingView(TemplateView):
    template_name = 'core/view_landing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Landing'
        return context


urlpatterns = [
    path('', LandingView.as_view(), name='home'),
]

urlpatterns += form_cruise.urlpatterns