"""URLs defined for celery.

* ``/$task_id/done/``
    URL to :func:`~celery.views.is_successful`.
* ``/$task_id/status/``
    URL  to :func:`~celery.views.task_status`.
"""

from django.urls import path, register_converter

from . import views


class TaskPatternConverter:
    """Custom path converter for task & group id's.

    They are slightly different from the built `uuid`
    """

    regex = r'[\w\d\-\.]+'

    def to_python(self, value):
        """Convert url to python value."""
        return str(value)

    def to_url(self, value):
        """Convert python value into url, just a string."""
        return value


register_converter(TaskPatternConverter, 'task_pattern')

urlpatterns = [
    # Old
    path(
        '<task_pattern:task_id>/done/',
        views.is_task_successful,
        name='celery-is_task_successful'
    ),
    path(
        '<task_pattern:task_id>/status/',
        views.task_status,
        name='celery-task_status'
    ),
    path(
        '<task_pattern:group_id>/group/done/',
        views.is_group_successful,
        name='celery-is_group_successful'
    ),
    path(
        '<task_patern:group_id>/group/status/',
        views.group_status,
        name='celery-group_status'
    ),

    # New
    path(
        'task/done/<task_pattern:task_id>/',
        views.is_task_successful,
        name='celery-is_task_successful'
    ),
    path(
        'task/status/<task_pattern:task_id>/',
        views.task_status,
        name='celery-task_status'
    ),
    path(
        'group/done/<task_pattern:group_id>/',
        views.is_group_successful,
        name='celery-is_group_successful'
    ),
    path(
        'group/status/<task_patern:group_id> /',
        views.group_status,
        name='celery-group_status'
    ),
]
