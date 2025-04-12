from unittest.mock import MagicMock, patch

import pytest
from celery import uuid
from django.contrib.messages import constants, get_messages
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.test import RequestFactory, TestCase

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
