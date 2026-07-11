"""
tracker/admin.py

Django admin configuration for the Personal Finance Tracker.

Each model admin is tuned for:
  - Readable list displays
  - Efficient filtering and searching
  - Inline relationships where helpful
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum
from .models import Category, Transaction, Budget


# ─────────────────────────────────────────────────────────────
#  Category Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display  = ('color_swatch', 'name', 'icon', 'owner', 'is_predefined', 'transaction_count')
    list_filter   = ('is_predefined',)
    search_fields = ('name', 'user__username')
    ordering      = ('name',)

    fieldsets = (
        (None, {
            'fields': ('name', 'icon', 'color')
        }),
        ('Ownership', {
            'fields': ('user', 'is_predefined'),
            'description': 'Leave "user" empty and check "is predefined" to make this category global.'
        }),
    )

    def color_swatch(self, obj):
        """Render a colored square next to the category name."""
        return format_html(
            '<span style="display:inline-block;width:16px;height:16px;'
            'border-radius:3px;background:{};vertical-align:middle;'
            'margin-right:6px;"></span>',
            obj.color
        )
    color_swatch.short_description = ''

    def owner(self, obj):
        return obj.user.username if obj.user else '— global —'
    owner.short_description = 'Owner'

    def transaction_count(self, obj):
        return obj.transactions.count()
    transaction_count.short_description = 'Transactions'


# ─────────────────────────────────────────────────────────────
#  Transaction Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display   = ('date', 'user', 'type_badge', 'amount_display', 'category', 'description_short')
    list_filter    = ('type', 'category', 'date')
    search_fields  = ('user__username', 'description', 'category__name')
    date_hierarchy = 'date'
    ordering       = ('-date',)
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Core', {
            'fields': ('user', 'type', 'amount', 'category', 'date')
        }),
        ('Details', {
            'fields': ('description',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def type_badge(self, obj):
        color = '#2dc653' if obj.type == 'income' else '#e63946'
        label = obj.get_type_display()
        return format_html(
            '<span style="padding:2px 8px;border-radius:12px;'
            'background:{};color:#fff;font-size:11px;font-weight:600;">{}</span>',
            color, label
        )
    type_badge.short_description = 'Type'

    def amount_display(self, obj):
        color = '#2dc653' if obj.type == 'income' else '#e63946'
        sign  = '+' if obj.type == 'income' else '-'
        return format_html(
            '<strong style="color:{};">{} ₹{:,.2f}</strong>',
            color, sign, obj.amount
        )
    amount_display.short_description = 'Amount'

    def description_short(self, obj):
        return obj.description[:50] + '…' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


# ─────────────────────────────────────────────────────────────
#  Budget Admin
# ─────────────────────────────────────────────────────────────

@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display  = ('user', 'category', 'period', 'amount', 'spent_display',
                     'percent_display', 'alert_status')
    list_filter   = ('month', 'year', 'category')
    search_fields = ('user__username', 'category__name')
    ordering      = ('-year', '-month')
    readonly_fields = ('warning_sent', 'critical_sent', 'created_at', 'updated_at')

    fieldsets = (
        ('Budget Definition', {
            'fields': ('user', 'category', 'amount', 'month', 'year')
        }),
        ('Alert Tracking', {
            'fields': ('warning_sent', 'critical_sent'),
            'classes': ('collapse',),
            'description': 'These flags prevent duplicate alert emails.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def period(self, obj):
        import calendar
        month_name = calendar.month_abbr[obj.month]
        return f"{month_name} {obj.year}"
    period.short_description = 'Period'

    def spent_display(self, obj):
        return f"₹{obj.spent:,.2f}"
    spent_display.short_description = 'Spent'

    def percent_display(self, obj):
        pct = min(obj.percentage_used, 100)
        color = '#e63946' if pct >= 100 else '#f77f00' if pct >= 80 else '#2dc653'
        return format_html(
            '<span style="color:{};">{:.1f}%</span>',
            color, obj.percentage_used
        )
    percent_display.short_description = '% Used'

    def alert_status(self, obj):
        level = obj.alert_level
        mapping = {
            'critical': ('<span style="color:#e63946;font-weight:700;">🔴 OVER BUDGET</span>'),
            'warning':  ('<span style="color:#f77f00;font-weight:700;">🟡 WARNING</span>'),
            'ok':       ('<span style="color:#2dc653;">🟢 OK</span>'),
        }
        return format_html(mapping[level])
    alert_status.short_description = 'Status'


# ─────────────────────────────────────────────────────────────
#  Admin site branding
# ─────────────────────────────────────────────────────────────

admin.site.site_header  = 'Finance Tracker Admin'
admin.site.site_title   = 'Finance Tracker'
admin.site.index_title  = 'Administration Panel'
