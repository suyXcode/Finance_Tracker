"""
tracker/apps.py

App configuration for the 'tracker' application.
Signals are connected here on app startup.
"""

from django.apps import AppConfig


class TrackerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tracker'
    verbose_name = 'Personal Finance Tracker'

    def ready(self):
        """
        Import signals module when the app is ready.
        This connects all signal handlers (budget alerts, etc.).
        """
        import tracker.signals  # noqa: F401
