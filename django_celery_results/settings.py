from collections.abc import Mapping

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_callback_function(settings_name, default=None):
    """Return the callback function for the given settings name."""
    callback = getattr(settings, settings_name, None)
    if not callback:
        return default

    if not callable(callback):
        raise ImproperlyConfigured(f"{settings_name} must be callable.")

    return callback


extend_task_props_callback = get_callback_function(
    "CELERY_RESULTS_EXTEND_TASK_PROPS_CALLBACK"
)


def get_task_props_extension(request, task_props):
    """Extend the task properties with custom props to fill custom models."""
    if not extend_task_props_callback:
        return {}

    task_props_extension = extend_task_props_callback(request, task_props) or {}
    if not isinstance(task_props_extension, Mapping):
        raise ImproperlyConfigured(
            "CELERY_RESULTS_EXTEND_TASK_PROPS_CALLBACK must return a Mapping "
            "instance."
        )

    return task_props_extension
