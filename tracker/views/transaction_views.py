"""
tracker/views/transaction_views.py

Transaction CRUD views:
  - TransactionListView    — paginated, filterable list
  - TransactionCreateView  — add new transaction
  - TransactionUpdateView  — edit existing transaction
  - TransactionDeleteView  — delete with confirmation
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.http import Http404
from django.conf import settings

from tracker.models import Transaction
from tracker.forms import TransactionForm, TransactionFilterForm
from tracker.services import get_transaction_queryset


class TransactionListView(LoginRequiredMixin, ListView):
    """
    Paginated, filterable transaction list.
    Supports filtering by type, category, date range, and description search.
    """
    template_name   = 'tracker/transactions/list.html'
    context_object_name = 'transactions'
    paginate_by     = 20  # overridden by settings.TRANSACTIONS_PER_PAGE

    def get_paginate_by(self, queryset):
        return getattr(settings, 'TRANSACTIONS_PER_PAGE', 20)

    def get_queryset(self):
        self.filter_form = TransactionFilterForm(
            self.request.GET or None,
            user=self.request.user
        )
        filters = None
        if self.filter_form.is_valid():
            filters = self.filter_form.cleaned_data
        return get_transaction_queryset(self.request.user, filters)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['filter_form'] = self.filter_form
        ctx['page_title']  = 'Transactions'
        # Preserve filter params in pagination links
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        ctx['query_string'] = query_params.urlencode()
        return ctx


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Add a new transaction."""
    model         = Transaction
    form_class    = TransactionForm
    template_name = 'tracker/transactions/form.html'
    success_url   = reverse_lazy('tracker:transaction_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Transaction added successfully.')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Add Transaction'
        ctx['action']     = 'Add'
        return ctx


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Edit an existing transaction — only owner can edit."""
    model         = Transaction
    form_class    = TransactionForm
    template_name = 'tracker/transactions/form.html'
    success_url   = reverse_lazy('tracker:transaction_list')

    def get_queryset(self):
        # Restrict to current user's transactions
        return Transaction.objects.filter(user=self.request.user)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Edit Transaction'
        ctx['action']     = 'Update'
        return ctx


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a transaction with a confirmation page."""
    model         = Transaction
    template_name = 'tracker/transactions/confirm_delete.html'
    success_url   = reverse_lazy('tracker:transaction_list')

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Transaction deleted.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Delete Transaction'
        return ctx
