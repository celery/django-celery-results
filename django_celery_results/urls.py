"""URLs defined for celery.

* ``/$task_id/done/``
    URL to :func:`~celery.views.is_successful`.
* ``/$task_id/status/``
    URL  to :func:`~celery.views.task_status`.
"""

from django.conf.urls import url, path

from . import views

task_pattern = r'(?P<task_id>[\w\d\-\.]+)'

urlpatterns = [
    url(
        r'^%s/done/?$' % task_pattern,
        views.is_task_successful,
        name='celery-is_task_successful'
    ),
    url(
        r'^%s/status/?$' % task_pattern,
        views.task_status,
        name='celery-task_status'
    ),
    path(
        r'<str:group_id>/group/done/',
        views.is_group_successful,
        name='celery-is_group_successful'
    ),
    path(
        r'<str:group_id>/group/status/',
        views.group_status,
        name='celery-group_status'
    ),
]
