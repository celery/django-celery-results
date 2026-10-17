from django.db import models

from django_celery_results.models.abstract import AbstractTaskResult


class ExtendedTaskResult(AbstractTaskResult):
    tenant_id = models.IntegerField(null=True)

    class Meta(AbstractTaskResult.Meta):
        abstract = False
        app_label = 'result_models'
        indexes = []
