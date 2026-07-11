"""
tracker/forms.py

All ModelForms for the Personal Finance Tracker.
Forms handle validation, widget customization, and user-scoped querysets.
"""

import calendar
from datetime import date
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Category, Transaction, Budget


# ─────────────────────────────────────────────────────────────
#  Shared Mixins
# ─────────────────────────────────────────────────────────────

class BootstrapMixin:
    """Add Bootstrap 5 'form-control' / 'form-select' classes to all fields."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                widget.attrs.setdefault('class', 'form-select')
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(widget, forms.Textarea):
                widget.attrs.setdefault('class', 'form-control')
                widget.attrs.setdefault('rows', 3)
            else:
                widget.attrs.setdefault('class', 'form-control')


# ─────────────────────────────────────────────────────────────
#  Authentication Forms
# ─────────────────────────────────────────────────────────────

class RegisterForm(BootstrapMixin, UserCreationForm):
    """User registration with email field."""

    email      = forms.EmailField(required=True, help_text='Required. A valid email address.')
    first_name = forms.CharField(max_length=50, required=False)
    last_name  = forms.CharField(max_length=50, required=False)

    class Meta:
        model  = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError('An account with this email address already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email      = self.cleaned_data['email'].lower()
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name  = self.cleaned_data.get('last_name', '')
        if commit:
            user.save()
        return user


class LoginForm(BootstrapMixin, AuthenticationForm):
    """Login form with Bootstrap styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['password'].widget.attrs['placeholder'] = 'Password'
        self.fields['username'].widget.attrs['autofocus']   = True


# ─────────────────────────────────────────────────────────────
#  Category Form
# ─────────────────────────────────────────────────────────────

class CategoryForm(BootstrapMixin, forms.ModelForm):
    """Create / edit a user-owned custom category."""

    class Meta:
        model  = Category
        fields = ('name', 'icon', 'color')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields['name'].widget.attrs['placeholder'] = 'e.g. Gym, Pet Care…'

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        qs = Category.objects.filter(user=self.user, name__iexact=name)
        # Exclude current instance when editing
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('You already have a category with this name.')
        return name

    def save(self, commit=True):
        category = super().save(commit=False)
        category.user          = self.user
        category.is_predefined = False
        if commit:
            category.save()
        return category


# ─────────────────────────────────────────────────────────────
#  Transaction Form
# ─────────────────────────────────────────────────────────────

class TransactionForm(BootstrapMixin, forms.ModelForm):
    """Add / edit a transaction. Category choices are scoped to the user."""

    class Meta:
        model  = Transaction
        fields = ('type', 'amount', 'category', 'date', 'description')
        widgets = {
            'date':        forms.DateInput(attrs={'type': 'date'}),
            'description': forms.TextInput(),  # single-line input
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        # Show only categories accessible to this user
        if user:
            self.fields['category'].queryset = Category.get_for_user(user)

        self.fields['category'].empty_label   = '— Select category —'
        self.fields['type'].widget.attrs['class'] = 'form-select'
        self.fields['amount'].widget.attrs['min']  = '0.01'
        self.fields['amount'].widget.attrs['step'] = '0.01'
        self.fields['description'].widget.attrs['placeholder'] = 'Optional note…'

        # Pre-fill date with today if creating new
        if not self.instance.pk:
            self.fields['date'].initial = date.today()

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount is not None and amount <= 0:
            raise ValidationError('Amount must be greater than zero.')
        return amount


# ─────────────────────────────────────────────────────────────
#  Transaction Filter Form (not a ModelForm — used for GET)
# ─────────────────────────────────────────────────────────────

class TransactionFilterForm(BootstrapMixin, forms.Form):
    """Filter bar on the transaction list page."""

    TYPE_CHOICES = [('', 'All Types')] + list(Transaction.TRANSACTION_TYPES)

    type        = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
    category    = forms.ModelChoiceField(queryset=Category.objects.none(), required=False,
                                          empty_label='All Categories')
    date_from   = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    date_to     = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    search      = forms.CharField(max_length=100, required=False,
                                   widget=forms.TextInput(attrs={'placeholder': 'Search description…'}))

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            self.fields['category'].queryset = Category.get_for_user(user)

    def clean(self):
        cleaned = super().clean()
        d_from  = cleaned.get('date_from')
        d_to    = cleaned.get('date_to')
        if d_from and d_to and d_from > d_to:
            raise ValidationError('"From" date cannot be after "To" date.')
        return cleaned


# ─────────────────────────────────────────────────────────────
#  Budget Form
# ─────────────────────────────────────────────────────────────

MONTH_CHOICES = [(i, calendar.month_name[i]) for i in range(1, 13)]
current_year  = date.today().year
YEAR_CHOICES  = [(y, str(y)) for y in range(current_year - 2, current_year + 3)]


class BudgetForm(BootstrapMixin, forms.ModelForm):
    """Create / edit a monthly budget per category."""

    month = forms.ChoiceField(choices=MONTH_CHOICES)
    year  = forms.ChoiceField(choices=YEAR_CHOICES)

    class Meta:
        model  = Budget
        fields = ('category', 'amount', 'month', 'year')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

        if user:
            self.fields['category'].queryset = Category.get_for_user(user)

        self.fields['category'].empty_label  = '— Select category —'
        self.fields['amount'].widget.attrs['min']  = '0.01'
        self.fields['amount'].widget.attrs['step'] = '0.01'

        # Default to current month/year
        today = date.today()
        self.fields['month'].initial = today.month
        self.fields['year'].initial  = today.year

    def clean(self):
        cleaned  = super().clean()
        category = cleaned.get('category')
        month    = cleaned.get('month')
        year     = cleaned.get('year')

        if category and month and year:
            qs = Budget.objects.filter(
                user=self.user,
                category=category,
                month=int(month),
                year=int(year),
            )
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError(
                    f'A budget for {category.name} in {calendar.month_name[int(month)]} '
                    f'{year} already exists.'
                )
        return cleaned

    def save(self, commit=True):
        budget          = super().save(commit=False)
        budget.user     = self.user
        budget.month    = int(self.cleaned_data['month'])
        budget.year     = int(self.cleaned_data['year'])
        # Reset alert flags when budget is edited (amount may have changed)
        budget.warning_sent  = False
        budget.critical_sent = False
        if commit:
            budget.save()
        return budget
