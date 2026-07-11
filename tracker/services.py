"""
tracker/services.py

Business logic layer — pure functions and query helpers.
Views call these instead of embedding logic directly.
All functions are user-scoped and return clean Python data structures.
"""

from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
import calendar

from .models import Transaction, Budget, Category


# ─────────────────────────────────────────────────────────────
#  Summary Calculations
# ─────────────────────────────────────────────────────────────

def get_summary(user, month=None, year=None):
    """
    Return total income, total expense, and net balance for a user.
    Optionally filter by month/year; defaults to current month.

    Returns:
        dict with keys: total_income, total_expense, net_balance
    """
    today = date.today()
    month = month or today.month
    year  = year  or today.year

    qs = Transaction.objects.filter(
        user=user,
        date__month=month,
        date__year=year,
    )

    totals = qs.aggregate(
        income  = Sum('amount', filter=Q(type=Transaction.INCOME)),
        expense = Sum('amount', filter=Q(type=Transaction.EXPENSE)),
    )

    income  = totals['income']  or Decimal('0.00')
    expense = totals['expense'] or Decimal('0.00')

    return {
        'total_income':   income,
        'total_expense':  expense,
        'net_balance':    income - expense,
        'month':          month,
        'year':           year,
        'month_name':     calendar.month_name[month],
    }


def get_all_time_summary(user):
    """Total income, expense, and balance across all time."""
    totals = Transaction.objects.filter(user=user).aggregate(
        income  = Sum('amount', filter=Q(type=Transaction.INCOME)),
        expense = Sum('amount', filter=Q(type=Transaction.EXPENSE)),
    )
    income  = totals['income']  or Decimal('0.00')
    expense = totals['expense'] or Decimal('0.00')
    return {
        'total_income':  income,
        'total_expense': expense,
        'net_balance':   income - expense,
    }


# ─────────────────────────────────────────────────────────────
#  Budget Tracking
# ─────────────────────────────────────────────────────────────

def get_budget_progress(user, month=None, year=None):
    """
    Return a list of budgets with their spending progress for a given month.

    Each item in the returned list is an augmented Budget instance with the
    `spent` and `percentage_used` properties evaluated.

    Returns:
        list of Budget objects (with .spent etc. as properties)
    """
    today = date.today()
    month = month or today.month
    year  = year  or today.year

    return Budget.objects.filter(
        user=user, month=month, year=year
    ).select_related('category').order_by('category__name')


def check_budget_alerts(transaction):
    """
    After saving an expense transaction, check whether any budget
    thresholds have been crossed and return a list of alert dicts.

    Called from signals.py — returns data; signal handler sends emails.

    Returns:
        list of dicts: [{budget, level, percentage_used}, ...]
    """
    from django.conf import settings

    if transaction.type != Transaction.EXPENSE:
        return []

    alerts = []

    try:
        budget = Budget.objects.get(
            user=transaction.user,
            category=transaction.category,
            month=transaction.date.month,
            year=transaction.date.year,
        )
    except Budget.DoesNotExist:
        return []

    pct = budget.percentage_used
    warning_threshold  = getattr(settings, 'BUDGET_WARNING_THRESHOLD',  80)
    critical_threshold = getattr(settings, 'BUDGET_CRITICAL_THRESHOLD', 100)

    # Critical: >= 100% and not already sent
    if pct >= critical_threshold and not budget.critical_sent:
        alerts.append({'budget': budget, 'level': 'critical', 'percentage': pct})
        budget.critical_sent = True
        budget.save(update_fields=['critical_sent'])

    # Warning: >= 80% but < 100% and not already sent
    elif pct >= warning_threshold and not budget.warning_sent:
        alerts.append({'budget': budget, 'level': 'warning', 'percentage': pct})
        budget.warning_sent = True
        budget.save(update_fields=['warning_sent'])

    return alerts


# ─────────────────────────────────────────────────────────────
#  Chart Data — JSON-serializable structures
# ─────────────────────────────────────────────────────────────

def get_category_spending_data(user, month=None, year=None):
    """
    Pie chart: expense breakdown by category for a given month.

    Returns:
        list of [category_name, amount_float]  (Google Charts DataTable format)
    """
    today = date.today()
    month = month or today.month
    year  = year  or today.year

    rows = (
        Transaction.objects.filter(
            user=user,
            type=Transaction.EXPENSE,
            date__month=month,
            date__year=year,
        )
        .values('category__name')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )

    data = []
    for row in rows:
        name  = row['category__name'] or 'Uncategorized'
        total = float(row['total'] or 0)
        data.append([name, total])

    return data


def get_monthly_trend_data(user, months=6):
    """
    Line chart: income vs expense over the last N months.

    Returns:
        {
          labels: ['Jan 24', 'Feb 24', ...],
          income:  [float, ...],
          expense: [float, ...]
        }
    """
    today = date.today()
    labels, income_vals, expense_vals = [], [], []

    for i in range(months - 1, -1, -1):
        # Go back i months from today
        target_month = today.month - i
        target_year  = today.year
        while target_month <= 0:
            target_month += 12
            target_year  -= 1

        label = f"{calendar.month_abbr[target_month]} {str(target_year)[-2:]}"
        labels.append(label)

        qs = Transaction.objects.filter(
            user=user,
            date__month=target_month,
            date__year=target_year,
        )
        totals = qs.aggregate(
            inc=Sum('amount', filter=Q(type=Transaction.INCOME)),
            exp=Sum('amount', filter=Q(type=Transaction.EXPENSE)),
        )
        income_vals.append(float(totals['inc']  or 0))
        expense_vals.append(float(totals['exp'] or 0))

    return {'labels': labels, 'income': income_vals, 'expense': expense_vals}


def get_weekly_spending_data(user, weeks=8):
    """
    Bar chart: total expenses by week (Mon–Sun) for the last N weeks.

    Returns:
        list of ['Week label', expense_float]
    """
    today = date.today()
    data  = []

    # Align to Monday of current week
    monday = today - timedelta(days=today.weekday())

    for i in range(weeks - 1, -1, -1):
        week_start = monday - timedelta(weeks=i)
        week_end   = week_start + timedelta(days=6)

        total = Transaction.objects.filter(
            user=user,
            type=Transaction.EXPENSE,
            date__gte=week_start,
            date__lte=week_end,
        ).aggregate(total=Sum('amount'))['total'] or 0

        label = week_start.strftime('%b %d')
        data.append([label, float(total)])

    return data


# ─────────────────────────────────────────────────────────────
#  Dashboard helpers
# ─────────────────────────────────────────────────────────────

def get_recent_transactions(user, limit=10):
    """Return the most recent N transactions for the dashboard."""
    return (
        Transaction.objects
        .filter(user=user)
        .select_related('category')
        .order_by('-date', '-created_at')[:limit]
    )


def get_transaction_queryset(user, filters=None):
    """
    Return a filtered, ordered queryset of transactions for a user.
    `filters` is a cleaned_data dict from TransactionFilterForm.
    """
    qs = Transaction.objects.filter(user=user).select_related('category')

    if not filters:
        return qs

    if filters.get('type'):
        qs = qs.filter(type=filters['type'])

    if filters.get('category'):
        qs = qs.filter(category=filters['category'])

    if filters.get('date_from'):
        qs = qs.filter(date__gte=filters['date_from'])

    if filters.get('date_to'):
        qs = qs.filter(date__lte=filters['date_to'])

    if filters.get('search'):
        qs = qs.filter(description__icontains=filters['search'])

    return qs
