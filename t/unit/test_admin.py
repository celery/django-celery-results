from unittest.mock import MagicMock, patch

import pytest
from celery import uuid
from django.contrib.messages import constants, get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

from django.apps import apps
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import (
    clear_url_caches,
    get_resolver,
    path,
    reverse,
)


from django_celery_results.admin import TaskResultAdmin
from django_celery_results.models import TaskResult


@pytest.mark.usefixtures('depends_on_current_app')
class test_Admin(TestCase):

    def setUp(self):
        self.task_admin = TaskResultAdmin(model=TaskResult, admin_site=None)
        self.factory = RequestFactory()

    def _apply_middleware(self, request):
        SessionMiddleware(lambda req: None).process_request(request)
        MessageMiddleware(lambda req: None).process_request(request)
        request.session.save()

    def create_task_result(self):
        id = uuid()
        taskmeta, created = TaskResult.objects.get_or_create(task_id=id)
        return taskmeta

    @patch('celery.current_app.control.terminate')
    def test_terminate_task_success(self, mock_terminate):
        # Create mock request
        request = self.factory.post('/')
        request.user = MagicMock()
        self._apply_middleware(request)

        # Create mock queryset
        tr1 = self.create_task_result()
        tr2 = self.create_task_result()
        task_id_list = [tr1.task_id, tr2.task_id]

        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = task_id_list

        # Call the terminate_task method
        self.task_admin.terminate_task(request, mock_queryset)

        # Verify terminate was called with the correct task IDs
        mock_terminate.assert_called_once_with(task_id_list)

        # Verify message_user was called with the success message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(
            str(messages[0]),
            "2 Task was terminated successfully.")
        self.assertEqual(messages[0].level, constants.SUCCESS)

    @patch('celery.current_app.control.terminate')
    def test_terminate_task_failure(self, mock_terminate):
        # Create mock request
        request = self.factory.post('/')
        request.user = MagicMock()
        self._apply_middleware(request)

        # Create mock queryset
        tr1 = self.create_task_result()
        tr2 = self.create_task_result()
        task_id_list = [tr1.task_id, tr2.task_id]

        mock_queryset = MagicMock()
        mock_queryset.values_list.return_value = task_id_list

        # Simulate an exception in terminate
        mock_terminate.side_effect = Exception("Termination failed")

        # Call the terminate_task method
        self.task_admin.terminate_task(request, mock_queryset)

        # Verify terminate was called with the correct task IDs
        mock_terminate.assert_called_once_with(task_id_list)

        # Verify message_user was called with the error message
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertIn(
            str(messages[0]),
            "Error while terminating tasks: Termination failed")
        self.assertEqual(messages[0].level, constants.ERROR)

User = get_user_model()


class TaskResultAdminTests(TestCase):
    app_name = "django_celery_results"
    model = TaskResult

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="password"
        )
        self.client.login(username="admin", password="password")
        self.task_result = TaskResult.objects.create(
            task_id=uuid(), task_name="test_task"
        )

    def test_add_view(self):
        url = reverse(
            f"admin:{self.app_name}_{self.model._meta.model_name}_add"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_view(self):
        url = reverse(
            f"admin:{self.app_name}_{self.model._meta.model_name}_change",
            args=[self.task_result.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TaskResultProxyAdminTests(TaskResultAdminTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        class TaskResultProxy(TaskResult):
            class Meta:
                proxy = True
                app_label = "django_celery_results"

        cls.model = TaskResultProxy
        admin.site.register(TaskResultProxy, TaskResultAdmin)

        # The temporary registration of admin requires refreshing the URL cache
        # Otherwise, it cannot be resolved
        default_resolver = get_resolver()
        cls.ori_url_patterns_0 = default_resolver.url_patterns[0]
        get_resolver().url_patterns[0] = path("admin/", admin.site.urls)
        clear_url_caches()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        # Unregister the proxy model
        admin.site.unregister(cls.model)
        app_config = apps.get_app_config(cls.app_name)
        model_name = cls.model._meta.model_name
        if model_name in app_config.models:
            del app_config.models[model_name]

        # Restore the original URL patterns
        get_resolver().url_patterns[0] = cls.ori_url_patterns_0
        clear_url_caches()

