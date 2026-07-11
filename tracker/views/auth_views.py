"""
tracker/views/auth_views.py

Authentication views: register, login, logout, password change.
Uses Django's built-in auth machinery with custom forms.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView
)
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View

from tracker.forms import RegisterForm, LoginForm


class RegisterView(View):
    """User registration — creates account and logs in immediately."""

    template_name = 'registration/register.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('tracker:dashboard')
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name or user.username}! Your account is ready.')
            return redirect('tracker:dashboard')
        return render(request, self.template_name, {'form': form})


class CustomLoginView(LoginView):
    """Login with custom Bootstrap-styled form."""
    form_class    = LoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {form.get_user().username}!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid username or password. Please try again.')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """Logout and redirect to login page with a goodbye message."""

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, 'You have been logged out successfully.')
        return super().dispatch(request, *args, **kwargs)


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change.html'
    success_url   = reverse_lazy('auth:password_change_done')

    def form_valid(self, form):
        messages.success(self.request, 'Your password was changed successfully.')
        return super().form_valid(form)


class CustomPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'
