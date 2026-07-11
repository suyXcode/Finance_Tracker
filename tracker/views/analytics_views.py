"""
tracker/views/analytics_views.py

Analytics dashboard view — serves the page that loads Google Charts.
Chart data is fetched asynchronously via JSON endpoints.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone


class AnalyticsView(LoginRequiredMixin, TemplateView):
    """
    Analytics page with Google Charts.
    The template loads chart data from JSON API endpoints via fetch().
    """
    template_name = 'tracker/analytics.html'

    def get_context_data(self, **kwargs):
        ctx   = super().get_context_data(**kwargs)
        now   = timezone.now()
        ctx['page_title']     = 'Analytics'
        ctx['current_month']  = now.month
        ctx['current_year']   = now.year
        return ctx
