from __future__ import absolute_import, unicode_literals

import warnings

from functools import wraps
from itertools import count

from django.db import connection, connections, router, transaction
from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings

from celery.five import items
from celery.utils.timeutils import maybe_timedelta

from .utils import now

W_ISOLATION_REP = """
Polling results with transaction isolation level 'repeatable-read'
within the same transaction may give outdated results.

Be sure to commit the transaction for each poll iteration.
"""


class TxIsolationWarning(UserWarning):
    pass


def transaction_retry(max_retries=1):
    """Decorator for functions doing database operations, adding
    retrying if the oepration fails.

    Keyword Arguments:
        max_retries (int): Maximum number of retries.  Default one retry.
    """
    def _outer(fun):

        @wraps(fun)
        def _inner(*args, **kwargs):
            _max_retries = kwargs.pop('exception_retry_count', max_retries)
            for retries in count(0):
                try:
                    return fun(*args, **kwargs)
                except Exception:   # pragma: no cover
                    # Depending on the database backend used we can experience
                    # various exceptions. E.g. psycopg2 raises an exception
                    # if some operation breaks the transaction, so saving
                    # the task result won't be possible until we rollback
                    # the transaction.
                    if retries >= _max_retries:
                        raise
        return _inner

    return _outer


class ExtendedQuerySet(QuerySet):

    def update_or_create(self, defaults=None, **kwargs):
        obj, created = self.get_or_create(defaults=defaults, **kwargs)
        if not created:
            self._update_model_with_dict(obj, dict(defaults or {}, **kwargs))
        return obj

    def _update_model_with_dict(self, obj, fields):
        [setattr(obj, attr_name, attr_value)
         for attr_name, attr_value in items(fields)]
        obj.save()
        return obj


class ExtendedManager(models.Manager.from_queryset(ExtendedQuerySet)):

    def connection_for_write(self):
        if connections:
            return connections[router.db_for_write(self.model)]
        return connection

    def connection_for_read(self):
        if connections:
            return connections[self.db]
        return connection

    def current_engine(self):
        try:
            return settings.DATABASES[self.db]['ENGINE']
        except AttributeError:
            return settings.DATABASE_ENGINE


class ResultManager(ExtendedManager):

    def get_all_expired(self, expires):
        """Get all expired task results."""
        return self.filter(date_done__lt=now() - maybe_timedelta(expires))

    def delete_expired(self, expires):
        """Delete all expired group results."""
        meta = self.model._meta
        with transaction.atomic():
            self.get_all_expired(expires).update(hidden=True)
            cursor = self.connection_for_write().cursor()
            cursor.execute(
                'DELETE FROM {0.db_table} WHERE hidden=%s'.format(meta),
                (True, ),
            )


class TaskResultManager(ResultManager):
    """Manager for :class:`celery.models.TaskResult` models."""
    _last_id = None

    def get_task(self, task_id):
        """Get task meta for task by ``task_id``.

        Keyword Arguments:
            exception_retry_count (int): How many times to retry by
                transaction rollback on exception.  This could
                happen in a race condition if another worker is trying to
                create the same task.  The default is to retry once.
        """
        try:
            return self.get(task_id=task_id)
        except self.model.DoesNotExist:
            if self._last_id == task_id:
                self.warn_if_repeatable_read()
            self._last_id = task_id
            return self.model(task_id=task_id)

    @transaction_retry(max_retries=2)
    def store_result(self, task_id, result, status,
                     traceback=None, children=None):
        """Store the result and status of a task.

        Arguments:
            task_id (str): Id of task.
            result (Any): The return value of the task, or an exception
                instance raised by the task.
            status (str): Task status.  See :mod:`celery.states` for a list of
                possible status values.

        Keyword Arguments:
            traceback (str): The traceback string taken at the point of
                exception (only passed if the task failed).
            children (Sequence): List of serialized results of subtasks
                of this task.
            exception_retry_count (int): How many times to retry by
                transaction rollback on exception.  This could
                happen in a race condition if another worker is trying to
                create the same task.  The default is to retry twice.
        """
        return self.update_or_create(task_id=task_id, defaults={
            'status': status,
            'result': result,
            'traceback': traceback,
            'meta': {'children': children},
        })

    def warn_if_repeatable_read(self):
        if 'mysql' in self.current_engine().lower():
            cursor = self.connection_for_read().cursor()
            if cursor.execute('SELECT @@tx_isolation'):
                isolation = cursor.fetchone()[0]
                if isolation == 'REPEATABLE-READ':
                    warnings.warn(TxIsolationWarning(W_ISOLATION_REP.strip()))


class GroupResultManager(ResultManager):
    """Manager for :class:`celery.models.GroupResult` models."""

    def restore_group(self, group_id):
        """Get the async result instance by group id."""
        try:
            return self.get(group_id=group_id)
        except self.model.DoesNotExist:
            pass
    restore_taskset = restore_group

    def delete_group(self, group_id):
        """Delete a saved group result."""
        s = self.restore_group(group_id)
        if s:
            s.delete()
    delete_taskset = delete_group

    @transaction_retry(max_retries=2)
    def store_result(self, group_id, result):
        """Store the async result instance of a group.

        Arguments:
            group_id (str): Id of group.
            result (celery.result.GroupResult): Group result instance.
        """
        return self.update_or_create(group_id=group_id, defaults={
            'result': result,
        })
