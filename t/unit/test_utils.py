from celery import uuid
from django.test import TransactionTestCase

from django_celery_results.models import TaskResult
from django_celery_results.utils import raw_delete

_TEST_RECORDS_COUNT = 100


class RawDeleteTest(TransactionTestCase):
    """Unit test for `utils.raw_delete` func."""

    def setUp(self):
        # setup test results to be used against raw_delete
        results = TaskResult.objects.bulk_create(
            [TaskResult(task_id=uuid()) for _ in range(_TEST_RECORDS_COUNT)]
        )
        assert TaskResult.objects.count() == _TEST_RECORDS_COUNT

    def test_all_rows_delete(self):
        raw_delete(
            queryset=TaskResult.objects.all()
        )
        assert TaskResult.objects.count() == 0

    def test_correct_rows_delete(self):
        # get random 10 rows
        sample_count = 10
        sample_result_ids = TaskResult.objects.values_list("pk").all().order_by("?")[:sample_count]
        # update task_name to "test"
        TaskResult.objects.filter(pk__in=sample_result_ids).update(task_name="test")
        # "raw delete" results with name = "test"
        raw_delete(
            queryset=TaskResult.objects.filter(task_name="test")
        )
        assert TaskResult.objects.filter(task_name="test").count() == 0
        assert TaskResult.objects.count() == (_TEST_RECORDS_COUNT - sample_count)
