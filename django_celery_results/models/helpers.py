from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

from .generic import ChordCounter, GroupResult, TaskResult


def _configured_model(setting_name, default_model):
    """Return the model configured by setting_name or default_model."""
    model_label = getattr(settings, setting_name, None)
    if model_label is None:
        return default_model

    try:
        return apps.get_model(model_label)
    except ValueError as exc:
        raise ImproperlyConfigured(
            f"{setting_name} must be of the form app_label.ModelName; "
            f"got {model_label!r}"
        ) from exc
    except LookupError as exc:
        raise ImproperlyConfigured(
            f"{setting_name} refers to model {model_label!r} that has not "
            "been installed"
        ) from exc


def taskresult_model():
    """Return the TaskResult model that is active in this project."""
    return _configured_model(
        'CELERY_RESULTS_TASKRESULT_MODEL',
        TaskResult,
    )


def chordcounter_model():
    """Return the ChordCounter model that is active in this project."""
    return _configured_model(
        'CELERY_RESULTS_CHORDCOUNTER_MODEL',
        ChordCounter,
    )


def groupresult_model():
    """Return the GroupResult model that is active in this project."""
    return _configured_model(
        'CELERY_RESULTS_GROUPRESULT_MODEL',
        GroupResult,
    )
