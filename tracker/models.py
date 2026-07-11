"""
tracker/models.py

Database schema for the Personal Finance Tracker.

Models:
    Category    — predefined + custom transaction categories
    Transaction — income/expense records
    Budget      — monthly budget limits per category per user

All models are user-scoped: every record belongs to a specific User.
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import datetime


# ─────────────────────────────────────────────────────────────
#  Category
# ─────────────────────────────────────────────────────────────

class Category(models.Model):
    """
    Represents a transaction category (e.g. Food, Rent, Salary).

    Categories can be:
      - Predefined (is_predefined=True, user=None): shared across all users
      - Custom      (is_predefined=False, user=<user>): private to one user

    The unique_together constraint prevents a user from creating two
    categories with the same name.
    """

    # Bootstrap icon class name (e.g. "bi-cart", "bi-house")
    ICON_CHOICES = [
        ('bi-cart',           'Shopping Cart'),
        ('bi-house',          'House / Rent'),
        ('bi-car-front',      'Transport'),
        ('bi-heart-pulse',    'Health'),
        ('bi-mortarboard',    'Education'),
        ('bi-controller',     'Entertainment'),
        ('bi-lightning',      'Utilities'),
        ('bi-briefcase',      'Work / Salary'),
        ('bi-piggy-bank',     'Savings'),
        ('bi-gift',           'Gifts'),
        ('bi-airplane',       'Travel'),
        ('bi-three-dots',     'Other'),
    ]

    COLOR_CHOICES = [
        ('#4361ee', 'Blue'),
        ('#f72585', 'Pink'),
        ('#4cc9f0', 'Cyan'),
        ('#7209b7', 'Purple'),
        ('#f77f00', 'Orange'),
        ('#2dc653', 'Green'),
        ('#e63946', 'Red'),
        ('#adb5bd', 'Gray'),
        ('#ffd60a', 'Yellow'),
        ('#06d6a0', 'Teal'),
    ]

    user          = models.ForeignKey(
                        User,
                        on_delete=models.CASCADE,
                        null=True,
                        blank=True,
                        related_name='categories',
                        help_text="Null for predefined/global categories"
                    )
    name          = models.CharField(max_length=100)
    icon          = models.CharField(max_length=50, choices=ICON_CHOICES, default='bi-three-dots')
    color         = models.CharField(max_length=7,  choices=COLOR_CHOICES, default='#4361ee')
    is_predefined = models.BooleanField(
                        default=False,
                        help_text="Predefined categories are available to all users"
                    )
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']
        # A user cannot have two categories with the same name.
        # (user=None, name='Food') is allowed once — that's the predefined entry.
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'name'],
                name='unique_category_per_user',
                condition=models.Q(user__isnull=False),
            ),
        ]

    def __str__(self):
        return self.name

    @classmethod
    def get_for_user(cls, user):
        """
        Return all categories available to a user:
        global predefined ones + their own custom ones.
        """
        return cls.objects.filter(
            models.Q(is_predefined=True) | models.Q(user=user)
        )


# ─────────────────────────────────────────────────────────────
#  Transaction
# ─────────────────────────────────────────────────────────────

class Transaction(models.Model):
    """
    A single financial event: either income or an expense.

    Constraints:
      - amount  must be > 0
      - type    must be 'income' or 'expense'
    """

    INCOME  = 'income'
    EXPENSE = 'expense'
    TRANSACTION_TYPES = [
        (INCOME,  'Income'),
        (EXPENSE, 'Expense'),
    ]

    user        = models.ForeignKey(
                      User,
                      on_delete=models.CASCADE,
                      related_name='transactions'
                  )
    category    = models.ForeignKey(
                      Category,
                      on_delete=models.SET_NULL,
                      null=True,
                      blank=True,
                      related_name='transactions'
                  )
    amount      = models.DecimalField(
                      max_digits=12,
                      decimal_places=2,
                      validators=[MinValueValidator(Decimal('0.01'))],
                      help_text="Must be greater than zero"
                  )
    type        = models.CharField(
                      max_length=10,
                      choices=TRANSACTION_TYPES,
                      db_index=True
                  )
    date        = models.DateField(default=datetime.date.today, db_index=True)
    description = models.CharField(max_length=255, blank=True, default='')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes  = [
            models.Index(fields=['user', 'type']),
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'category']),
        ]

    def __str__(self):
        return f"{self.get_type_display()} | {self.amount} | {self.date}"

    @property
    def is_income(self):
        return self.type == self.INCOME

    @property
    def is_expense(self):
        return self.type == self.EXPENSE


# ─────────────────────────────────────────────────────────────
#  Budget
# ─────────────────────────────────────────────────────────────

class Budget(models.Model):
    """
    A monthly spending limit for one category for one user.

    The unique_together constraint (user, category, month, year)
    ensures only one budget record per category per month per user.

    Business logic (percentage_used, alert status) lives as model
    properties so it can be reused across views and signals.
    """

    user      = models.ForeignKey(
                    User,
                    on_delete=models.CASCADE,
                    related_name='budgets'
                )
    category  = models.ForeignKey(
                    Category,
                    on_delete=models.CASCADE,
                    related_name='budgets'
                )
    amount    = models.DecimalField(
                    max_digits=12,
                    decimal_places=2,
                    validators=[MinValueValidator(Decimal('0.01'))],
                    help_text="Monthly budget limit (must be > 0)"
                )
    month     = models.PositiveSmallIntegerField(
                    help_text="Month number 1–12"
                )
    year      = models.PositiveSmallIntegerField(
                    help_text="4-digit year, e.g. 2024"
                )

    # Tracks whether warning / critical emails have already been sent
    # this month to avoid spamming the user.
    warning_sent  = models.BooleanField(default=False)
    critical_sent = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-year', '-month', 'category__name']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'category', 'month', 'year'],
                name='unique_budget_per_category_month_year'
            ),
        ]

    def __str__(self):
        return (
            f"{self.user.username} | {self.category.name} | "
            f"{self.month}/{self.year} | limit={self.amount}"
        )

    # ── Computed properties ──────────────────────────────────

    @property
    def spent(self):
        """
        Total expenses in this category for this month/year.
        Queries the database — call sparingly in tight loops.
        """
        result = Transaction.objects.filter(
            user=self.user,
            category=self.category,
            type=Transaction.EXPENSE,
            date__month=self.month,
            date__year=self.year,
        ).aggregate(total=models.Sum('amount'))['total']
        return result or Decimal('0.00')

    @property
    def remaining(self):
        """Amount left in the budget (can be negative if over-budget)."""
        return self.amount - self.spent

    @property
    def percentage_used(self):
        """
        Percentage of budget consumed.
        Returns 0 if budget amount is 0 (safety guard).
        Capped display value: returns actual float, callers handle capping.
        """
        if self.amount <= 0:
            return 0
        return round(float(self.spent / self.amount * 100), 1)

    @property
    def is_over_budget(self):
        return self.spent >= self.amount

    @property
    def alert_level(self):
        """
        Returns 'critical', 'warning', or 'ok'.
        Used by templates to pick progress bar color.
        """
        pct = self.percentage_used
        if pct >= 100:
            return 'critical'
        if pct >= 80:
            return 'warning'
        return 'ok'

    @property
    def progress_bar_class(self):
        """Bootstrap progress bar color class."""
        mapping = {
            'critical': 'bg-danger',
            'warning':  'bg-warning',
            'ok':       'bg-success',
        }
        return mapping[self.alert_level]

    @classmethod
    def get_current_month_budgets(cls, user):
        """Convenience: all budgets for user in the current month/year."""
        now = timezone.now()
        return cls.objects.filter(
            user=user,
            month=now.month,
            year=now.year,
        ).select_related('category')
