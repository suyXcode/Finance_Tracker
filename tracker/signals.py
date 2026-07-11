"""
tracker/signals.py

Django signals for the Finance Tracker.
Listens to Transaction post_save and sends HTML budget alert emails.
"""

import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

from .models import Transaction

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Transaction)
def transaction_saved_handler(sender, instance, created, **kwargs):
    """Fires after every Transaction save — checks budget thresholds."""
    if instance.type != Transaction.EXPENSE:
        return
    if not instance.category:
        return
    from .services import check_budget_alerts
    try:
        alerts = check_budget_alerts(instance)
        for alert in alerts:
            _send_budget_alert_email(alert, instance.user)
    except Exception as exc:
        logger.error('Budget alert check failed for transaction %s: %s', instance.pk, exc, exc_info=True)


def _send_budget_alert_email(alert, user):
    """Render and dispatch an HTML budget alert email."""
    budget     = alert['budget']
    level      = alert['level']
    percentage = alert['percentage']

    subject_map  = {
        'warning':  f'\u26a0\ufe0f Budget Warning: {budget.category.name} at {percentage:.0f}%',
        'critical': f'\U0001f6a8 Budget Exceeded: {budget.category.name} at {percentage:.0f}%',
    }
    template_map = {
        'warning':  'email/budget_warning.html',
        'critical': 'email/budget_critical.html',
    }
    context = {
        'user': user, 'budget': budget, 'percentage': percentage,
        'spent': budget.spent, 'remaining': budget.remaining, 'level': level,
    }
    html_body  = render_to_string(template_map[level], context)
    plain_body = strip_tags(html_body)
    recipient  = user.email
    if not recipient:
        logger.warning('User %s has no email — skipping alert.', user.username)
        return
    try:
        send_mail(
            subject=subject_map[level], message=plain_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient], html_message=html_body, fail_silently=False,
        )
        logger.info('Budget %s alert sent to %s', level, recipient)
    except Exception as exc:
        logger.error('Failed to send budget alert to %s: %s', recipient, exc)
