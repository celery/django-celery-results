import time
from datetime import timedelta

import pytest
from celery import uuid
from django.test import TransactionTestCase

from django_celery_results.models import TaskResult
from django_celery_results.utils import now

RECORDS_COUNT = 100000


@pytest.fixture()
def use_benchmark(request, benchmark):
    def wrapped(a=10, b=5):
        return a + b
    request.cls.benchmark = benchmark


@pytest.mark.usefixtures('use_benchmark')
@pytest.mark.usefixtures('depends_on_current_app')
class benchmark_Models(TransactionTestCase):

    @pytest.fixture(autouse=True)
    def setup_app(self, app):
        self.app = app
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend')

    def create_many_task_result(self, count):
        start = time.time()
        draft_results = [TaskResult(task_id=uuid()) for _ in range(count)]
        drafted = time.time()
        results = TaskResult.objects.bulk_create(draft_results)
        done_creating = time.time()

        print((
            'drafting time: {drafting:.2f}\n'
            'bulk_create time: {done:.2f}\n'
            '------'
        ).format(drafting=drafted - start, done=done_creating - drafted))
        return results

    def setup_records_to_delete(self):
        self.create_many_task_result(count=RECORDS_COUNT)
        mid_point = TaskResult.objects.order_by('id')[int(RECORDS_COUNT / 2)]
        todelete = TaskResult.objects.filter(id__gte=mid_point.id)
        todelete.update(date_done=now() - timedelta(days=10))

    def test_taskresult_delete_expired(self):
        start = time.time()
        self.setup_records_to_delete()
        after_setup = time.time()
        self.benchmark.pedantic(
            TaskResult.objects.delete_expired,
            args=(self.app.conf.result_expires,),
            iterations=1,
            rounds=1,
        )
        done = time.time()
        assert TaskResult.objects.count() == int(RECORDS_COUNT / 2)

        print((
            '------'
            'setup time: {setup:.2f}\n'
            'bench time: {bench:.2f}\n'
        ).format(setup=after_setup - start, bench=done - after_setup))
        assert self.benchmark.stats.stats.max < 1
