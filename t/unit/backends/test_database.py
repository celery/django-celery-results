from __future__ import absolute_import, unicode_literals

import mock
import celery
import pytest

from celery import uuid
from celery import states

from django_celery_results.backends.database import DatabaseBackend


class SomeClass(object):

    def __init__(self, data):
        self.data = data


@pytest.mark.django_db()
@pytest.mark.usefixtures('depends_on_current_app')
class test_DatabaseBackend:

    @pytest.fixture(autouse=True)
    def setup_backend(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend')
        self.b = DatabaseBackend(app=self.app)

    def test_backend__pickle_serialization__dict_result(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        result = {'foo': 'baz', 'bar': SomeClass(12345)}
        request = mock.MagicMock()
        request.task = 'my_task'
        request.args = ['a', 1, SomeClass(67)]
        request.kwargs = {'c': 6, 'd': 'e', 'f': SomeClass(89)}
        request.hostname = 'celery@ip-0-0-0-0'
        del request.argsrepr, request.kwargsrepr

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar').data == 12345
        assert mindb.get('task_name') == 'my_task'

        assert len(mindb.get('task_args')) == 3
        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert len(mindb.get('task_kwargs')) == 3
        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid3, exception)

        assert self.b.get_status(tid3) == states.FAILURE
        assert isinstance(self.b.get_result(tid3), KeyError)

    def test_backend__pickle_serialization__str_result(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        result = 'foo'
        request = mock.MagicMock()
        request.task = 'my_task'
        request.args = ['a', 1, SomeClass(67)]
        request.kwargs = {'c': 6, 'd': 'e', 'f': SomeClass(89)}
        request.hostname = 'celery@ip-0-0-0-0'
        del request.argsrepr, request.kwargsrepr

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'

        assert len(mindb.get('task_args')) == 3
        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert len(mindb.get('task_kwargs')) == 3
        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

    def test_backend__pickle_serialization__bytes_result(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        result = b'foo'
        request = mock.MagicMock()
        request.task = 'my_task'
        request.args = ['a', 1, SomeClass(67)]
        request.kwargs = {'c': 6, 'd': 'e', 'f': SomeClass(89)}
        request.hostname = 'celery@ip-0-0-0-0'
        del request.argsrepr, request.kwargsrepr

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        assert mindb.get('result') == b'foo'
        assert mindb.get('task_name') == 'my_task'

        assert len(mindb.get('task_args')) == 3
        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert len(mindb.get('task_kwargs')) == 3
        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

    def xxx_backend(self):
        tid = uuid()

        assert self.b.get_status(tid) == states.PENDING
        assert self.b.get_result(tid) is None

        self.b.mark_as_done(tid, 42)
        assert self.b.get_status(tid) == states.SUCCESS
        assert self.b.get_result(tid) == 42

        tid2 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid2, exception)

        assert self.b.get_status(tid2) == states.FAILURE
        assert isinstance(self.b.get_result(tid2), KeyError)

    def test_forget(self):
        tid = uuid()
        self.b.mark_as_done(tid, {'foo': 'bar'})
        x = self.app.AsyncResult(tid)
        assert x.result.get('foo') == 'bar'
        x.forget()
        if celery.VERSION[0:3] == (3, 1, 10):
            # bug in 3.1.10 means result did not clear cache after forget.
            x._cache = None
        assert x.result is None

    def test_backend_secrets(self):
        tid = uuid()
        request = mock.MagicMock()
        request.task = 'my_task'
        request.args = ['a', 1, 'password']
        request.kwargs = {'c': 3, 'd': 'e', 'password': 'password'}
        request.argsrepr = 'argsrepr'
        request.kwargsrepr = 'kwargsrepr'
        request.hostname = 'celery@ip-0-0-0-0'
        result = {'foo': 'baz'}

        self.b.mark_as_done(tid, result, request=request)

        mindb = self.b.get_task_meta(tid)
        assert mindb.get('task_args') == 'argsrepr'
        assert mindb.get('task_kwargs') == 'kwargsrepr'
        assert mindb.get('worker') == 'celery@ip-0-0-0-0'
