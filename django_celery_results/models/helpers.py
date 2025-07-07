from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .generic import ChordCounter, GroupResult, TaskResult


def taskresult_model():
    """Return the TaskResult model that is active in this project."""
    if not hasattr(settings, 'CELERY_RESULTS_TASKRESULT_MODEL'):
        return TaskResult

    try:
        return apps.get_model(
            settings.CELERY_RESULTS_TASKRESULT_MODEL
        )
    except ValueError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_TASKRESULT_MODEL must be of the form "
            "'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_TASKRESULT_MODEL refers to model "
            f"'{settings.CELERY_RESULTS_TASKRESULT_MODEL}' that has not "
            "been installed"
        )


def chordcounter_model():
    """Return the ChordCounter model that is active in this project."""

    if not hasattr(settings, 'CELERY_RESULTS_CHORDCOUNTER_MODEL'):
        return ChordCounter

    try:
        return apps.get_model(
            settings.CELERY_RESULTS_CHORDCOUNTER_MODEL
        )
    except ValueError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_CHORDCOUNTER_MODEL must be of the form "
            "'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_CHORDCOUNTER_MODEL refers to model "
            f"'{settings.CELERY_RESULTS_CHORDCOUNTER_MODEL}' that has not "
            "been installed"
        )


def groupresult_model():
    """Return the GroupResult model that is active in this project."""
    if not hasattr(settings, 'CELERY_RESULTS_GROUPRESULT_MODEL'):
        return GroupResult

    try:
        return apps.get_model(
            settings.CELERY_RESULTS_GROUPRESULT_MODEL
        )
    except ValueError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_GROUPRESULT_MODEL must be of the form "
            "'app_label.model_name'"
        )
    except LookupError:
        raise ImproperlyConfigured(
            "CELERY_RESULTS_GROUPRESULT_MODEL refers to model "
            f"'{settings.CELERY_RESULTS_GROUPRESULT_MODEL}' that has not "
            "been installed"
        )
