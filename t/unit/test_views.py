from __future__ import absolute_import, unicode_literals

import json
import pytest

from django.test import TestCase
from django.test.client import RequestFactory

from celery import states, uuid

from django_celery_results.models import TaskResult
from django_celery_results.views import is_task_successful, task_status


@pytest.mark.usefixtures('depends_on_current_app')
class test_Views(TestCase):
    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        self.app = app
        self.app.conf.result_serializer = 'json'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend'
        )

    def setUp(self):
        self.factory = RequestFactory()

    def create_task_result(self):
        id = uuid()
        taskmeta, created = TaskResult.objects.get_or_create(task_id=id)
        return taskmeta

    def test_is_task_successful(self):
        taskmeta = self.create_task_result()
        request = self.factory.get('/done/{}'.format(taskmeta.task_id))
        response = is_task_successful(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['executed'] is False

        TaskResult.objects.store_result(
            'application/json',
            'utf-8',
            taskmeta.task_id,
            json.dumps({'result': True}),
            status=states.SUCCESS
        )

        request = self.factory.get('/done/{}'.format(taskmeta.task_id))
        response = is_task_successful(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['executed'] is True

    def test_task_status(self):
        taskmeta = self.create_task_result()
        request = self.factory.get('/status/{}'.format(taskmeta.task_id))
        response = task_status(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['status'] is not states.SUCCESS

        TaskResult.objects.store_result(
            'application/json',
            'utf-8',
            taskmeta.task_id,
            json.dumps({'result': True}),
            status=states.SUCCESS
        )

        request = self.factory.get('/status/{}'.format(taskmeta.task_id))
        response = task_status(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['status'] == states.SUCCESS
