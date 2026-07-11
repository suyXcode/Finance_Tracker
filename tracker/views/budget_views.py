"""
tracker/views/budget_views.py

Budget management views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils import timezone

from tracker.models import Budget
from tracker.forms import BudgetForm
from tracker.services import get_budget_progress


class BudgetListView(LoginRequiredMixin, ListView):
    """List all budgets for the current month."""
    template_name       = 'tracker/budgets/list.html'
    context_object_name = 'budgets'

    def get_queryset(self):
        now = timezone.now()
        return Budget.objects.filter(
            user=self.request.user,
            month=now.month,
            year=now.year,
        ).select_related('category').order_by('category__name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Budgets'
        now = timezone.now()
        ctx['current_month'] = now.month
        ctx['current_year']  = now.year

        import calendar
        ctx['month_name'] = calendar.month_name[now.month]

        # All-time budget list for the filter panel
        ctx['all_budgets'] = Budget.objects.filter(
            user=self.request.user
        ).select_related('category').order_by('-year', '-month')
        return ctx


class BudgetCreateView(LoginRequiredMixin, CreateView):
    """Set a new monthly budget."""
    model         = Budget
    form_class    = BudgetForm
    template_name = 'tracker/budgets/form.html'
    success_url   = reverse_lazy('tracker:budget_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Budget created successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Set Budget'
        ctx['action']     = 'Create'
        return ctx


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing budget."""
    model         = Budget
    form_class    = BudgetForm
    template_name = 'tracker/budgets/form.html'
    success_url   = reverse_lazy('tracker:budget_list')

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Budget updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Edit Budget'
        ctx['action']     = 'Update'
        return ctx


class BudgetDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a budget."""
    model         = Budget
    template_name = 'tracker/budgets/confirm_delete.html'
    success_url   = reverse_lazy('tracker:budget_list')

    def get_queryset(self):
        return Budget.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Budget deleted.')
        return super().form_valid(form)
