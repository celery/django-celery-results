from __future__ import absolute_import, unicode_literals

import celery

from celery import uuid
from celery import states
from celery.tests.case import AppCase

from django_celery_results.backends.database import DatabaseBackend


class SomeClass(object):

    def __init__(self, data):
        self.data = data


class test_DatabaseBackend(AppCase):

    def setup(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend')
        self.app.set_current()
        self.app.set_default()
        self.b = DatabaseBackend(app=self.app)

    def test_backend__pickle_serialization(self):
        self.app.conf.result_serializer = 'pickle'
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        self.b.mark_as_done(tid2, result)
        # is serialized properly.
        rindb = self.b.get_result(tid2)
        self.assertEqual(rindb.get('foo'), 'baz')
        self.assertEqual(rindb.get('bar').data, 12345)

        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid3, exception)

        self.assertEqual(self.b.get_status(tid3), states.FAILURE)
        self.assertIsInstance(self.b.get_result(tid3), KeyError)

    def xxx_backend(self):
        tid = uuid()

        self.assertEqual(self.b.get_status(tid), states.PENDING)
        self.assertIsNone(self.b.get_result(tid))

        self.b.mark_as_done(tid, 42)
        self.assertEqual(self.b.get_status(tid), states.SUCCESS)
        self.assertEqual(self.b.get_result(tid), 42)

        tid2 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid2, exception)

        self.assertEqual(self.b.get_status(tid2), states.FAILURE)
        self.assertIsInstance(self.b.get_result(tid2), KeyError)

    def test_forget(self):
        tid = uuid()
        self.b.mark_as_done(tid, {'foo': 'bar'})
        x = self.app.AsyncResult(tid)
        self.assertEqual(x.result.get('foo'), 'bar')
        x.forget()
        if celery.VERSION[0:3] == (3, 1, 10):
            # bug in 3.1.10 means result did not clear cache after forget.
            x._cache = None
        self.assertIsNone(x.result)
