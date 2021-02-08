"""URLs defined for celery.

* ``/$task_id/done/``
    URL to :func:`~celery.views.is_successful`.
* ``/$task_id/status/``
    URL  to :func:`~celery.views.task_status`.
"""

from django.conf.urls import path, register_converter

from . import views


class TaskPatternConverter:
    """
    custom path converter for task & group id's,
    then are slightly different from the built 'uuid'
    """

    regex = r'[\w\d\-\.]+'

    def to_python(self, value):
        """convert url to python value"""

        return str(value)

    def to_url(self, value):
        """convert python value into url, just a string"""

        return value


register_converter(TaskPatternConverter, 'task_pattern')

urlpatterns = [
    path(
        r'<task_pattern:task_id>/done/',
        views.is_task_successful,
        name='celery-is_task_successful'
    ),
    path(
        r'<task_pattern:task_id>/status/',
        views.task_status,
        name='celery-task_status'
    ),
    path(
        r'<task_pattern:group_id>/group/done/',
        views.is_group_successful,
        name='celery-is_group_successful'
    ),
    path(
        r'<task_patern:group_id>/group/status/',
        views.group_status,
        name='celery-group_status'
    ),
]
