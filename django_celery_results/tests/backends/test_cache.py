from __future__ import absolute_import, unicode_literals

import sys

from datetime import timedelta

from billiard.einfo import ExceptionInfo

from celery import result
from celery import states
from celery import uuid
from celery.tests.case import AppCase, depends_on_current_app

from django_celery_results.backends.cache import CacheBackend


class SomeClass(object):

    def __init__(self, data):
        self.data = data


class CacheCase(AppCase):

    def setUp(self):
        super(CacheCase, self).setUp()
        self.app.set_current()
        self.app.set_default()
        self.app.conf.update(
            result_serializer='pickle',
            result_backend='django_celery_results.backends:CacheBackend',
        )


class test_CacheBackend(AppCase):

    def setup(self):
        self.b = CacheBackend(app=self.app)

    def test_mark_as_done(self):
        tid = uuid()

        self.assertEqual(self.b.get_status(tid), states.PENDING)
        self.assertIsNone(self.b.get_result(tid))

        self.b.mark_as_done(tid, 42)
        self.assertEqual(self.b.get_status(tid), states.SUCCESS)
        self.assertEqual(self.b.get_result(tid), 42)
        self.assertTrue(self.b.get_result(tid), 42)

    def test_forget(self):
        tid = uuid()
        self.b.mark_as_done(tid, {'foo': 'bar'})
        self.assertEqual(self.b.get_result(tid).get('foo'), 'bar')
        self.b.forget(tid)
        self.assertNotIn(tid, self.b._cache)
        self.assertIsNone(self.b.get_result(tid))

    @depends_on_current_app
    def test_save_restore_delete_group(self):
        group_id = uuid()
        result_ids = [uuid() for i in range(10)]
        results = list(map(result.AsyncResult, result_ids))
        res = result.GroupResult(group_id, results)
        res.save(backend=self.b)
        saved = result.GroupResult.restore(group_id, backend=self.b)
        self.assertListEqual(saved.results, results)
        self.assertEqual(saved.id, group_id)
        saved.delete(backend=self.b)
        self.assertIsNone(result.GroupResult.restore(
            group_id, backend=self.b))

    def test_is_pickled(self):
        tid2 = uuid()
        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        self.b.mark_as_done(tid2, result)
        # is serialized properly.
        rindb = self.b.get_result(tid2)
        self.assertEqual(rindb.get('foo'), 'baz')
        self.assertEqual(rindb.get('bar').data, 12345)

    def test_mark_as_failure(self):
        einfo = None
        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            einfo = ExceptionInfo(sys.exc_info())
            self.b.mark_as_failure(tid3, exception, traceback=einfo.traceback)
        self.assertEqual(self.b.get_status(tid3), states.FAILURE)
        self.assertIsInstance(self.b.get_result(tid3), KeyError)
        self.assertEqual(self.b.get_traceback(tid3), einfo.traceback)

    def test_process_cleanup(self):
        self.b.process_cleanup()

    def test_set_expires(self):
        cb1 = CacheBackend(app=self.app, expires=timedelta(seconds=16))
        self.assertEqual(cb1.expires, 16)
        cb2 = CacheBackend(app=self.app, expires=32)
        self.assertEqual(cb2.expires, 32)


class test_custom_CacheBackend(AppCase):

    def test_custom_cache_backend(self):
        self.app.conf.cache_backend = 'dummy'
        b = CacheBackend(app=self.app)
        self.assertEqual(b.cache_backend.__class__.__module__,
                         'django.core.cache.backends.dummy')
