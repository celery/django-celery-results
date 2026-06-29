"""Application configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

__all__ = ['CeleryResultConfig']

from django_celery_results.conf import app_settings


class CeleryResultConfig(AppConfig):
    """Default configuration for the django_celery_results app."""

    name = 'django_celery_results'
    label = 'django_celery_results'
    verbose_name = _('Celery Results')
    default_auto_field = app_settings.DJANGO_CELERY_RESULTS_DEFAULT_AUTO_FIELD
