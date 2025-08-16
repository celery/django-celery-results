from celery import uuid
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
        default_resover = get_resolver()
        cls.ori_url_patterns_0 = default_resover.url_patterns[0]
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
