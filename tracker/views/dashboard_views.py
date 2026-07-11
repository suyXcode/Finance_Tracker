"""
tracker/views/dashboard_views.py

Dashboard view: aggregates summary stats, budget progress, and recent transactions.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from tracker.services import (
    get_summary,
    get_budget_progress,
    get_recent_transactions,
)


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard page.

    Context:
        summary      — income/expense/balance for current month
        budgets      — budget progress list
        transactions — 10 most recent transactions
    """
    template_name = 'tracker/dashboard.html'

    def get_context_data(self, **kwargs):
        ctx  = super().get_context_data(**kwargs)
        user = self.request.user

        ctx['summary']      = get_summary(user)
        ctx['budgets']      = get_budget_progress(user)
        ctx['transactions'] = get_recent_transactions(user, limit=10)
        ctx['page_title']   = 'Dashboard'

        return ctx
