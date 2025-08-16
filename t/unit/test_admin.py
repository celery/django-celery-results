import pytest
from celery import uuid
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from django_celery_results.admin import TaskResultAdmin
from django_celery_results.models import TaskResult

User = get_user_model()


@pytest.mark.usefixtures("depends_on_current_app")
class TaskResultAdminTests(TestCase):
    app_name = "django_celery_results"
    model_name = "taskresult"

    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="password"
        )
        self.client.login(username="admin", password="password")
        self.task_result = TaskResult.objects.create(
            task_id=uuid(), task_name="test_task"
        )

    def test_add_view(self):
        url = reverse(f"admin:{self.app_name}_{self.model_name}_add")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_change_view(self):
        url = reverse(
            f"admin:{self.app_name}_{self.model_name}_change",
            args=[self.task_result.id],
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)


class TaskResultProxy(TaskResult):
    class Meta:
        proxy = True
        app_label = "django_celery_results"


admin.site.register(TaskResultProxy, TaskResultAdmin)


class TaskResultProxyAdminTests(TaskResultAdminTests):
    model_name = "taskresultproxy"
