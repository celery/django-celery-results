from celery import uuid
from django.test import TransactionTestCase

from django_celery_results.models import TaskResult
from django_celery_results.utils import raw_delete

_TEST_RECORDS_COUNT = 100


class RawDeleteTest(TransactionTestCase):
    """Unit test for `utils.raw_delete` func."""

    def setUp(self):
        # setup test results to be used against raw_delete
        TaskResult.objects.bulk_create(
            [TaskResult(task_id=uuid()) for _ in range(_TEST_RECORDS_COUNT)]
        )
        assert TaskResult.objects.count() == _TEST_RECORDS_COUNT

    def _get_sample_result_ids(self, count):
        return TaskResult.objects.values_list("pk").order_by("?")[:count]

    def test_all_rows_delete(self):
        raw_delete(
            queryset=TaskResult.objects.all()
        )
        assert TaskResult.objects.count() == 0

    def test_correct_rows_deleted(self):
        # sample random 10 rows
        sample_size = 10
        sample_ids = self._get_sample_result_ids(count=sample_size)
        # update task_name to "test"
        TaskResult.objects.filter(pk__in=sample_ids).update(task_name="test")
        # "raw delete" results with name = "test"
        raw_delete(
            queryset=TaskResult.objects.filter(task_name="test")
        )
        assert TaskResult.objects.filter(task_name="test").count() == 0
        results_remaining = _TEST_RECORDS_COUNT - sample_size
        assert TaskResult.objects.count() == results_remaining
