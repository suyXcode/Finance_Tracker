"""
finance_tracker/urls.py

Root URL configuration for the Personal Finance Tracker project.
All app-level URLs are namespaced and included here.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Django admin
    path('admin/', admin.site.urls),

    # Authentication (register / login / logout / password change)
    path('auth/', include('tracker.urls.auth_urls', namespace='auth')),

    # Main application (dashboard, transactions, categories, budgets, exports)
    path('', include('tracker.urls.app_urls', namespace='tracker')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
