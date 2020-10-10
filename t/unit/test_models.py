from __future__ import absolute_import, unicode_literals

import pytest

from datetime import datetime, timedelta

from django.db import transaction
from django.test import TransactionTestCase

from celery import states, uuid

from django_celery_results.models import TaskResult
from django_celery_results.utils import now


@pytest.mark.usefixtures('depends_on_current_app')
class test_Models(TransactionTestCase):
    databases = '__all__'

    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        self.app = app
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend')

    def create_task_result(self):
        id = uuid()
        taskmeta, created = TaskResult.objects.get_or_create(task_id=id)
        return taskmeta

    def test_taskmeta(self, ctype='application/json', cenc='utf-8'):
        m1 = self.create_task_result()
        m2 = self.create_task_result()
        m3 = self.create_task_result()
        assert str(m1).startswith('<Task:')
        assert m1.task_id
        assert isinstance(m1.date_done, datetime)

        task = TaskResult.objects.get_task(m1.task_id)
        assert task._meta.get_field('task_id').max_length == 191
        assert task.task_id == m1.task_id
        assert task.status != states.SUCCESS
        TaskResult.objects.store_result(
            ctype, cenc, m1.task_id, True, status=states.SUCCESS)
        TaskResult.objects.store_result(
            ctype, cenc, m2.task_id, True, status=states.SUCCESS)
        assert TaskResult.objects.get_task(m1.task_id).status == states.SUCCESS
        assert TaskResult.objects.get_task(m2.task_id).status == states.SUCCESS

        # Have to avoid save() because it applies the auto_now=True.
        TaskResult.objects.filter(
            task_id=m1.task_id
        ).update(date_done=now() - timedelta(days=10))

        expired = TaskResult.objects.get_all_expired(
            self.app.conf.result_expires,
        )
        assert m1 in expired
        assert m2 not in expired
        assert m3 not in expired

        TaskResult.objects.delete_expired(
            self.app.conf.result_expires,
        )
        assert m1 not in TaskResult.objects.all()

    def test_store_result(self, ctype='application/json', cenc='utf-8'):
        """
        Test the `using` argument.
        With the `using` kwarg, we can specify the database to use for updating
        results. By specifying a different database than the one used by the
        transaction, we can bypass the transaction and update a result.
        This is useful for things like progress updates, where a long
        running transaction has not been committed, but we still want to
        allow clients to receive updates.
        """
        class TransactionError(Exception):
            pass

        m1 = self.create_task_result()
        m2 = self.create_task_result()
        assert set(TaskResult.objects.all()) == set(
            TaskResult.objects.using("secondary").all()
        )
        try:
            with transaction.atomic():
                TaskResult.objects.store_result(
                    ctype, cenc, m1.task_id, True, status=states.SUCCESS)
                TaskResult.objects.store_result(
                    ctype, cenc, m2.task_id, True, status=states.SUCCESS,
                    using='secondary')
                raise TransactionError()
        except TransactionError:
            pass

        assert TaskResult.objects.get_task(m1.task_id).status != states.SUCCESS
        assert TaskResult.objects.get_task(m2.task_id).status == states.SUCCESS
