from django.conf import settings


def get_callback_function(settings_name, default=None):
    """Return the callback function for the given settings name."""
    
    callback = getattr(settings, settings_name, None)
    if callback is None:
        return default

    if callable(callback):
        return callback

extend_task_props_callback = get_callback_function(
    "CELERY_RESULTS_EXTEND_TASK_PROPS_CALLBACK"
)