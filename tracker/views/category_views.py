"""
tracker/views/category_views.py

Category management views.
Predefined global categories are read-only; only custom (user-owned) ones
can be created, edited, or deleted.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.core.exceptions import PermissionDenied

from tracker.models import Category
from tracker.forms import CategoryForm


class CategoryListView(LoginRequiredMixin, ListView):
    """List all categories available to the user (predefined + custom)."""
    template_name       = 'tracker/categories/list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.get_for_user(self.request.user)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title']  = 'Categories'
        ctx['user_categories'] = self.get_queryset().filter(user=self.request.user)
        ctx['global_categories'] = self.get_queryset().filter(is_predefined=True)
        return ctx


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create a new custom category."""
    model         = Category
    form_class    = CategoryForm
    template_name = 'tracker/categories/form.html'
    success_url   = reverse_lazy('tracker:category_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" created.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'New Category'
        ctx['action']     = 'Create'
        return ctx


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Edit a custom category — only owner allowed."""
    model         = Category
    form_class    = CategoryForm
    template_name = 'tracker/categories/form.html'
    success_url   = reverse_lazy('tracker:category_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_predefined or obj.user != self.request.user:
            raise PermissionDenied('You cannot edit a predefined category.')
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, f'Category "{form.instance.name}" updated.')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'Edit Category'
        ctx['action']     = 'Update'
        return ctx


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    """Delete a user-owned custom category."""
    model         = Category
    template_name = 'tracker/categories/confirm_delete.html'
    success_url   = reverse_lazy('tracker:category_list')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.is_predefined or obj.user != self.request.user:
            raise PermissionDenied('You cannot delete a predefined category.')
        return obj

    def form_valid(self, form):
        messages.success(self.request, 'Category deleted.')
        return super().form_valid(form)
