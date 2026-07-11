"""
tracker/views/export_views.py

Export views for the Finance Tracker:
  - ExportCSVView   — all transactions as CSV
  - ExportPDFView   — monthly summary report as PDF (ReportLab)
"""

import csv
import io
import calendar
from datetime import date
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from tracker.models import Transaction
from tracker.services import get_summary, get_budget_progress, get_transaction_queryset


# ─────────────────────────────────────────────────────────────
#  CSV Export
# ─────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class ExportCSVView(View):
    """
    Export all transactions (or filtered subset) as a CSV file.
    Respects the same filters as the transaction list page.
    """

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = (
            f'attachment; filename="transactions_{date.today().isoformat()}.csv"'
        )

        writer = csv.writer(response)

        # Header row
        writer.writerow(['Date', 'Type', 'Category', 'Amount (INR)', 'Description'])

        # Data rows — all transactions for the user, newest first
        transactions = (
            Transaction.objects
            .filter(user=request.user)
            .select_related('category')
            .order_by('-date', '-created_at')
        )

        for txn in transactions:
            writer.writerow([
                txn.date.strftime('%Y-%m-%d'),
                txn.get_type_display(),
                txn.category.name if txn.category else 'Uncategorized',
                str(txn.amount),
                txn.description,
            ])

        return response


# ─────────────────────────────────────────────────────────────
#  PDF Monthly Report
# ─────────────────────────────────────────────────────────────

@method_decorator(login_required, name='dispatch')
class ExportPDFView(View):
    """
    Generate a polished monthly summary PDF report using ReportLab.
    Query params: ?month=M&year=Y (defaults to current month).
    """

    # Color palette
    DARK_BLUE  = colors.HexColor('#1e3a5f')
    ACCENT     = colors.HexColor('#4361ee')
    GREEN      = colors.HexColor('#2dc653')
    RED        = colors.HexColor('#e63946')
    LIGHT_GRAY = colors.HexColor('#f8f9fa')
    MID_GRAY   = colors.HexColor('#dee2e6')
    TEXT_DARK  = colors.HexColor('#212529')

    def get(self, request):
        today = date.today()
        try:
            month = int(request.GET.get('month', today.month))
            year  = int(request.GET.get('year',  today.year))
        except (ValueError, TypeError):
            month, year = today.month, today.year

        month_label = f"{calendar.month_name[month]} {year}"
        filename    = f"finance_report_{year}_{month:02d}.pdf"

        # Build PDF in memory
        buffer = io.BytesIO()
        doc    = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm,
        )

        story = self._build_story(request.user, month, year, month_label)
        doc.build(story)

        pdf = buffer.getvalue()
        buffer.close()

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    def _build_story(self, user, month, year, month_label):
        styles  = getSampleStyleSheet()
        story   = []
        summary = get_summary(user, month=month, year=year)
        budgets = list(get_budget_progress(user, month=month, year=year))

        transactions = list(
            Transaction.objects
            .filter(user=user, date__month=month, date__year=year)
            .select_related('category')
            .order_by('-date')
        )

        # ── Title Block ──────────────────────────────────────
        title_style = ParagraphStyle(
            'Title', fontName='Helvetica-Bold', fontSize=22,
            textColor=self.DARK_BLUE, alignment=TA_CENTER, spaceAfter=4
        )
        sub_style = ParagraphStyle(
            'Sub', fontName='Helvetica', fontSize=11,
            textColor=colors.gray, alignment=TA_CENTER, spaceAfter=16
        )
        story.append(Paragraph('Personal Finance Report', title_style))
        story.append(Paragraph(month_label, sub_style))
        story.append(Paragraph(f'Prepared for: {user.get_full_name() or user.username}', sub_style))
        story.append(HRFlowable(width='100%', thickness=2, color=self.ACCENT))
        story.append(Spacer(1, 0.4*cm))

        # ── Summary Cards ────────────────────────────────────
        section_style = ParagraphStyle(
            'Section', fontName='Helvetica-Bold', fontSize=13,
            textColor=self.DARK_BLUE, spaceBefore=10, spaceAfter=6
        )
        story.append(Paragraph('Monthly Summary', section_style))

        net_color = self.GREEN if summary['net_balance'] >= 0 else self.RED
        summary_data = [
            ['Metric', 'Amount'],
            ['Total Income',   f"₹{summary['total_income']:,.2f}"],
            ['Total Expenses', f"₹{summary['total_expense']:,.2f}"],
            ['Net Balance',    f"₹{summary['net_balance']:,.2f}"],
        ]
        summary_table = Table(summary_data, colWidths=[9*cm, 7*cm])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND',  (0, 0), (-1, 0),  self.DARK_BLUE),
            ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.white),
            ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
            ('FONTSIZE',    (0, 0), (-1, 0),  11),
            ('ALIGN',       (1, 0), (1, -1),  'RIGHT'),
            ('BACKGROUND',  (0, 1), (-1, 1),  colors.HexColor('#e8f5e9')),
            ('BACKGROUND',  (0, 2), (-1, 2),  colors.HexColor('#ffebee')),
            ('BACKGROUND',  (0, 3), (-1, 3),  self.LIGHT_GRAY),
            ('TEXTCOLOR',   (1, 3), (1, 3),   net_color),
            ('FONTNAME',    (0, 3), (-1, 3),  'Helvetica-Bold'),
            ('GRID',        (0, 0), (-1, -1), 0.5, self.MID_GRAY),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [None]),
            ('TOPPADDING',  (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.5*cm))

        # ── Budget Progress ──────────────────────────────────
        if budgets:
            story.append(Paragraph('Budget Progress', section_style))
            budget_data = [['Category', 'Budget', 'Spent', 'Remaining', 'Used %']]
            for b in budgets:
                pct      = b.percentage_used
                color_fn = self.RED if pct >= 100 else (colors.HexColor('#f77f00') if pct >= 80 else self.GREEN)
                budget_data.append([
                    b.category.name,
                    f'₹{b.amount:,.2f}',
                    f'₹{b.spent:,.2f}',
                    f'₹{b.remaining:,.2f}',
                    f'{pct:.1f}%',
                ])
            budget_table = Table(budget_data, colWidths=[5*cm, 3*cm, 3*cm, 3*cm, 3*cm])
            budget_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0),  self.DARK_BLUE),
                ('TEXTCOLOR',  (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',   (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('ALIGN',      (1, 0), (-1, -1), 'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
                ('GRID',       (0, 0), (-1, -1), 0.5, self.MID_GRAY),
                ('TOPPADDING', (0, 0), (-1, -1), 7),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(budget_table)
            story.append(Spacer(1, 0.5*cm))

        # ── Transaction Detail ───────────────────────────────
        if transactions:
            story.append(Paragraph('Transaction Details', section_style))
            txn_data = [['Date', 'Type', 'Category', 'Description', 'Amount']]
            for txn in transactions:
                txn_data.append([
                    txn.date.strftime('%d %b'),
                    txn.get_type_display(),
                    txn.category.name if txn.category else '—',
                    (txn.description[:30] + '…') if len(txn.description) > 30 else txn.description or '—',
                    f"₹{txn.amount:,.2f}",
                ])
            txn_table = Table(txn_data, colWidths=[2*cm, 2.2*cm, 3.5*cm, 6.3*cm, 3*cm])
            txn_table.setStyle(TableStyle([
                ('BACKGROUND',  (0, 0), (-1, 0),  self.ACCENT),
                ('TEXTCOLOR',   (0, 0), (-1, 0),  colors.white),
                ('FONTNAME',    (0, 0), (-1, 0),  'Helvetica-Bold'),
                ('FONTSIZE',    (0, 0), (-1, -1), 8),
                ('ALIGN',       (4, 0), (4, -1),  'RIGHT'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.LIGHT_GRAY]),
                ('GRID',        (0, 0), (-1, -1), 0.3, self.MID_GRAY),
                ('TOPPADDING',  (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ]))
            story.append(txn_table)

        # ── Footer ───────────────────────────────────────────
        story.append(Spacer(1, 0.5*cm))
        story.append(HRFlowable(width='100%', thickness=1, color=self.MID_GRAY))
        footer_style = ParagraphStyle(
            'Footer', fontName='Helvetica', fontSize=8,
            textColor=colors.gray, alignment=TA_CENTER, spaceBefore=6
        )
        story.append(Paragraph(
            f'Generated by Personal Finance Tracker • {date.today().strftime("%d %B %Y")}',
            footer_style
        ))

        return story
