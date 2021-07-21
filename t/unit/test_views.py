import json

import pytest
from celery import states, uuid
from celery.result import AsyncResult
from celery.result import GroupResult as CeleryGroupResult
from django.test import TestCase
from django.test.client import RequestFactory

from django_celery_results.models import GroupResult, TaskResult
from django_celery_results.views import (
    group_status,
    is_group_successful,
    is_task_successful,
    task_status,
)


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
        request = self.factory.get(f'/done/{taskmeta.task_id}')
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

        request = self.factory.get(f'/done/{taskmeta.task_id}')
        response = is_task_successful(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['executed'] is True

    def test_task_status(self):
        taskmeta = self.create_task_result()
        request = self.factory.get(f'/status/{taskmeta.task_id}')
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

        request = self.factory.get(f'/status/{taskmeta.task_id}')
        response = task_status(request, taskmeta.task_id)
        assert response
        result = json.loads(response.content.decode('utf-8'))
        assert result['task']['status'] == states.SUCCESS

    def create_group_result(self):
        """Return a GroupResult model instance
        with a single, successful result"""
        id = uuid()
        task_result = self.create_task_result()
        task_result.status = states.SUCCESS
        task_result.save()
        results = [AsyncResult(id=task_result.task_id)]
        group = CeleryGroupResult(id=id, results=results)
        group.save()
        meta = GroupResult.objects.get(group_id=id)
        return meta

    def test_is_group_successful(self):
        meta = self.create_group_result()
        request = self.factory.get(f'/group/done/{meta.group_id}')
        response = is_group_successful(request, meta.group_id)
        assert response

        result = json.loads(response.content.decode('utf-8'))
        assert len(result['group']['results']) == 1
        result = json.loads(response.content.decode('utf-8'))
        assert result['group']['results'][0]['executed'] is True

    def test_group_status(self):
        meta = self.create_group_result()
        request = self.factory.get(f'/group/status/{meta.group_id}')
        response = group_status(request, meta.group_id)
        assert response

        result = json.loads(response.content.decode('utf-8'))
        assert len(result["group"]["results"]) == 1
        assert result["group"]["results"][0]["status"] == states.SUCCESS
