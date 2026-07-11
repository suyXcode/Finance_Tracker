"""
tracker/views/chart_views.py

JSON API endpoints consumed by Google Charts on the Analytics page.
All endpoints require authentication and return user-scoped data only.
"""

import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from tracker.services import (
    get_category_spending_data,
    get_monthly_trend_data,
    get_weekly_spending_data,
)


@method_decorator(login_required, name='dispatch')
class CategorySpendingAPIView(View):
    """
    GET /api/charts/category-spending/?month=M&year=Y

    Returns Google Charts DataTable for pie chart.
    Response: { "data": [["Category", "Amount"], ["Food", 450.00], ...] }
    """

    def get(self, request):
        month = _int_param(request, 'month')
        year  = _int_param(request, 'year')

        rows = get_category_spending_data(request.user, month=month, year=year)

        # Google Charts expects the first row to be column headers
        data = [['Category', 'Amount']] + rows

        return JsonResponse({'data': data, 'status': 'ok'})


@method_decorator(login_required, name='dispatch')
class MonthlyTrendAPIView(View):
    """
    GET /api/charts/monthly-trend/?months=6

    Returns data for income/expense line chart over the last N months.
    Response: { "labels": [...], "income": [...], "expense": [...] }
    """

    def get(self, request):
        months = _int_param(request, 'months') or 6
        months = max(2, min(months, 24))  # clamp 2–24

        data = get_monthly_trend_data(request.user, months=months)
        return JsonResponse({**data, 'status': 'ok'})


@method_decorator(login_required, name='dispatch')
class WeeklySpendingAPIView(View):
    """
    GET /api/charts/weekly-spending/?weeks=8

    Returns data for bar chart of weekly expenses.
    Response: { "data": [["Week", "Expense"], ["Apr 01", 320.0], ...] }
    """

    def get(self, request):
        weeks = _int_param(request, 'weeks') or 8
        weeks = max(2, min(weeks, 16))

        rows = get_weekly_spending_data(request.user, weeks=weeks)
        data = [['Week Starting', 'Expenses']] + rows

        return JsonResponse({'data': data, 'status': 'ok'})


# ─── Helper ──────────────────────────────────────────────────

def _int_param(request, key, default=None):
    """Safely parse an integer query parameter."""
    val = request.GET.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default
