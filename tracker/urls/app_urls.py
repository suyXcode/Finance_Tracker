from django.urls import path
from tracker.views.dashboard_views    import DashboardView
from tracker.views.transaction_views  import (TransactionListView, TransactionCreateView,
                                               TransactionUpdateView, TransactionDeleteView)
from tracker.views.category_views     import (CategoryListView, CategoryCreateView,
                                               CategoryUpdateView, CategoryDeleteView)
from tracker.views.budget_views       import (BudgetListView, BudgetCreateView,
                                               BudgetUpdateView, BudgetDeleteView)
from tracker.views.chart_views        import (CategorySpendingAPIView, MonthlyTrendAPIView,
                                               WeeklySpendingAPIView)
from tracker.views.export_views       import ExportCSVView, ExportPDFView
from tracker.views.analytics_views    import AnalyticsView
from django.views.generic             import RedirectView

app_name = 'tracker'

urlpatterns = [
    # Root redirect
    path('', RedirectView.as_view(url='/dashboard/', permanent=False), name='home'),

    # Dashboard
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Analytics
    path('analytics/', AnalyticsView.as_view(), name='analytics'),

    # Transactions
    path('transactions/',                  TransactionListView.as_view(),   name='transaction_list'),
    path('transactions/add/',              TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/',    TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/',  TransactionDeleteView.as_view(), name='transaction_delete'),

    # Categories
    path('categories/',                 CategoryListView.as_view(),   name='category_list'),
    path('categories/add/',             CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/',   CategoryUpdateView.as_view(), name='category_edit'),
    path('categories/<int:pk>/delete/', CategoryDeleteView.as_view(), name='category_delete'),

    # Budgets
    path('budgets/',                 BudgetListView.as_view(),   name='budget_list'),
    path('budgets/add/',             BudgetCreateView.as_view(), name='budget_create'),
    path('budgets/<int:pk>/edit/',   BudgetUpdateView.as_view(), name='budget_edit'),
    path('budgets/<int:pk>/delete/', BudgetDeleteView.as_view(), name='budget_delete'),

    # Chart JSON APIs
    path('api/charts/category-spending/', CategorySpendingAPIView.as_view(), name='api_category_spending'),
    path('api/charts/monthly-trend/',     MonthlyTrendAPIView.as_view(),     name='api_monthly_trend'),
    path('api/charts/weekly-spending/',   WeeklySpendingAPIView.as_view(),   name='api_weekly_spending'),

    # Exports
    path('export/csv/', ExportCSVView.as_view(), name='export_csv'),
    path('export/pdf/', ExportPDFView.as_view(), name='export_pdf'),
]
