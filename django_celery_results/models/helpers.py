from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def taskresult_model():
    """Return the TaskResult model that is active in this project."""
    if not hasattr(settings, 'CELERY_RESULTS_TASKRESULT_MODEL'):
        from .generic import TaskResult

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
        from .generic import ChordCounter

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
        from .generic import GroupResult

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
