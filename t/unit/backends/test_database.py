import datetime
import json
import pickle
import re
from unittest import mock

import celery
import pytest
from celery import states, uuid
from celery.app.task import Context
from celery.result import AsyncResult, GroupResult
from celery.utils.serialization import b64decode
from celery.worker.request import Request
from celery.worker.strategy import hybrid_to_proto2
from django.test import TransactionTestCase

from django_celery_results.backends.database import DatabaseBackend
from django_celery_results.models import ChordCounter, TaskResult


class SomeClass:

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
        self.app.conf.result_extended = True
        self.b = DatabaseBackend(app=self.app)

    def _create_request(self, task_id, name, args, kwargs,
                        argsrepr=None, kwargsrepr=None, task_protocol=2):
        msg = self.app.amqp.task_protocols[task_protocol](
            task_id=task_id,
            name=name,
            args=args,
            kwargs=kwargs,
            argsrepr=argsrepr,
            kwargsrepr=kwargsrepr,
        )
        if task_protocol == 1:
            body, headers, _, _ = hybrid_to_proto2(msg, msg.body)
            properties = None
            sent_event = {}
        else:
            headers, properties, body, sent_event = msg
        context = Context(
            headers=headers,
            properties=properties,
            body=body,
            sent_event=sent_event,
        )
        request = Request(context, decoded=True, task=name)
        if task_protocol == 1:
            assert request.argsrepr is None
            assert request.kwargsrepr is None
        else:
            assert request.argsrepr is not None
            assert request.kwargsrepr is not None
        return request

    def test_backend__pickle_serialization__dict_result(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
        )
        result = {'foo': 'baz', 'bar': SomeClass(12345)}

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar').data == 12345
        assert len(mindb.get('worker')) > 1
        assert mindb.get('task_name') == 'my_task'
        assert bool(re.match(
            r"\['a', 1, <.*SomeClass object at .*>\]",
            mindb.get('task_args')
        ))
        assert bool(re.match(
            r"{'c': 6, 'd': 'e', 'f': <.*SomeClass object at .*>}",
            mindb.get('task_kwargs')
        ))

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

        # check async_result
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

        # check backward compatibility
        task_kwargs2 = str(request.kwargs)
        task_args2 = str(request.args)
        assert tr.task_args != task_args2
        assert tr.task_kwargs != task_kwargs2
        tr.task_args = task_args2
        tr.task_kwargs = task_kwargs2
        tr.save()
        mindb = self.b.get_task_meta(tid2)
        assert bool(re.match(
            r"\['a', 1, <.*SomeClass object at .*>\]",
            mindb.get('task_args')
        ))
        assert bool(re.match(
            r"{'c': 6, 'd': 'e', 'f': <.*SomeClass object at .*>}",
            mindb.get('task_kwargs')
        ))
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

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
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
        )
        result = 'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'
        assert len(mindb.get('worker')) > 1
        assert bool(re.match(
            r"\['a', 1, <.*SomeClass object at .*>\]",
            mindb.get('task_args')
        ))
        assert bool(re.match(
            r"{'c': 6, 'd': 'e', 'f': <.*SomeClass object at .*>}",
            mindb.get('task_kwargs')
        ))

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

        # check async_result
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

    def test_backend__pickle_serialization__bytes_result(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
        )
        result = b'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == b'foo'
        assert mindb.get('task_name') == 'my_task'
        assert len(mindb.get('worker')) > 1
        assert bool(re.match(
            r"\['a', 1, <.*SomeClass object at .*>\]",
            mindb.get('task_args')
        ))
        assert bool(re.match(
            r"{'c': 6, 'd': 'e', 'f': <.*SomeClass object at .*>}",
            mindb.get('task_kwargs')
        ))

        # check task_result objects
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

        # check async_result
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

    def test_backend__json_serialization__dict_result(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
        )
        result = {'foo': 'baz', 'bar': True}

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar') is True
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == "['a', 1, True]"
        assert mindb.get('task_kwargs') == "{'c': 6, 'd': 'e', 'f': False}"

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == "['a', 1, True]"
        assert json.loads(tr.task_kwargs) == "{'c': 6, 'd': 'e', 'f': False}"

        # check async_result
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

        # check backward compatibility
        task_kwargs2 = str(request.kwargs)
        task_args2 = str(request.args)
        assert tr.task_args != task_args2
        assert tr.task_kwargs != task_kwargs2
        tr.task_args = task_args2
        tr.task_kwargs = task_kwargs2
        tr.save()
        mindb = self.b.get_task_meta(tid2)
        assert mindb.get('task_args') == "['a', 1, True]"
        assert mindb.get('task_kwargs') == "{'c': 6, 'd': 'e', 'f': False}"
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid3, exception)

        assert self.b.get_status(tid3) == states.FAILURE
        assert isinstance(self.b.get_result(tid3), KeyError)

    def test_backend__json_serialization__str_result(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
        )
        result = 'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == "['a', 1, True]"
        assert mindb.get('task_kwargs') == "{'c': 6, 'd': 'e', 'f': False}"

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == "['a', 1, True]"
        assert json.loads(tr.task_kwargs) == "{'c': 6, 'd': 'e', 'f': False}"

        # check async_result
        ar = AsyncResult(tid2)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

    def test_backend__pickle_serialization__dict_result__protocol_1(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
            task_protocol=1,
        )
        result = {'foo': 'baz', 'bar': SomeClass(12345)}

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar').data == 12345
        assert mindb.get('task_name') == 'my_task'

        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        assert task_args[0] == 'a'
        assert task_args[1] == 1
        assert task_args[2].data == 67

        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_kwargs['c'] == 6
        assert task_kwargs['d'] == 'e'
        assert task_kwargs['f'].data == 89

        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid3, exception)

        assert self.b.get_status(tid3) == states.FAILURE
        assert isinstance(self.b.get_result(tid3), KeyError)

    def test_backend__pickle_serialization__str_result__protocol_1(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
            task_protocol=1,
        )
        result = 'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'

        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        assert task_args[0] == 'a'
        assert task_args[1] == 1
        assert task_args[2].data == 67

        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_kwargs['c'] == 6
        assert task_kwargs['d'] == 'e'
        assert task_kwargs['f'].data == 89

    def test_backend__pickle_serialization__bytes_result__protocol_1(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
            task_protocol=1,
        )
        result = b'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == b'foo'
        assert mindb.get('task_name') == 'my_task'

        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        assert task_args[0] == 'a'
        assert task_args[1] == 1
        assert task_args[2].data == 67

        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_kwargs['c'] == 6
        assert task_kwargs['d'] == 'e'
        assert task_kwargs['f'].data == 89

    def test_backend__json_serialization__dict_result__protocol_1(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
            task_protocol=1,
        )
        result = {'foo': 'baz', 'bar': True}

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar') is True
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == ['a', 1, True]
        assert mindb.get('task_kwargs') == {'c': 6, 'd': 'e', 'f': False}

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == ['a', 1, True]
        assert json.loads(tr.task_kwargs) == {'c': 6, 'd': 'e', 'f': False}

        tid3 = uuid()
        try:
            raise KeyError('foo')
        except KeyError as exception:
            self.b.mark_as_failure(tid3, exception)

        assert self.b.get_status(tid3) == states.FAILURE
        assert isinstance(self.b.get_result(tid3), KeyError)

    def test_backend__json_serialization__str_result__protocol_1(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
            task_protocol=1,
        )
        result = 'foo'

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == ['a', 1, True]
        assert mindb.get('task_kwargs') == {'c': 6, 'd': 'e', 'f': False}

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == ['a', 1, True]
        assert json.loads(tr.task_kwargs) == {'c': 6, 'd': 'e', 'f': False}

    def test_backend__task_result_meta_injection(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=[],
            kwargs={},
            task_protocol=1,
        )
        result = None

        # inject request meta arbitrary data
        request.meta = {
            'key': 'value'
        }

        self.b.mark_as_done(tid2, result, request=request)
        mindb = self.b.get_task_meta(tid2)

        # check task meta
        assert mindb.get('result') is None
        assert mindb.get('task_name') == 'my_task'

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.meta) == {'key': 'value', 'children': []}

    def test_backend__task_result_date(self):
        tid2 = uuid()

        self.b.store_result(tid2, None, states.PENDING)

        tr = TaskResult.objects.get(task_id=tid2)
        assert tr.status == states.PENDING
        assert isinstance(tr.date_created, datetime.datetime)
        assert tr.date_started is None
        assert isinstance(tr.date_done, datetime.datetime)

        date_created = tr.date_created
        date_done = tr.date_done

        self.b.mark_as_started(tid2)

        tr = TaskResult.objects.get(task_id=tid2)
        assert tr.status == states.STARTED
        assert date_created == tr.date_created
        assert isinstance(tr.date_started, datetime.datetime)
        assert tr.date_done > date_done

        date_started = tr.date_started
        date_done = tr.date_done

        self.b.mark_as_done(tid2, 42)

        tr = TaskResult.objects.get(task_id=tid2)
        assert tr.status == states.SUCCESS
        assert tr.date_created == date_created
        assert tr.date_started == date_started
        assert tr.date_done > date_done

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

    def test_secrets__pickle_serialization(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid = uuid()
        request = self._create_request(
            task_id=tid,
            name='my_task',
            args=['a', 1, 'password'],
            kwargs={'c': 3, 'd': 'e', 'password': 'password'},
            argsrepr='argsrepr',
            kwargsrepr='kwargsrepr',
        )
        result = {'foo': 'baz'}

        self.b.mark_as_done(tid, result, request=request)
        mindb = self.b.get_task_meta(tid)

        # check task meta
        assert mindb.get('result') == {'foo': 'baz'}
        assert mindb.get('task_args') == 'argsrepr'
        assert mindb.get('task_kwargs') == 'kwargsrepr'
        assert len(mindb.get('worker')) > 1

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == 'argsrepr'
        assert task_kwargs == 'kwargsrepr'

        # check async_result
        ar = AsyncResult(tid)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

    def test_secrets__json_serialization(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid = uuid()
        request = self._create_request(
            task_id=tid,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
            argsrepr='argsrepr',
            kwargsrepr='kwargsrepr',
        )
        result = {'foo': 'baz'}

        self.b.mark_as_done(tid, result, request=request)
        mindb = self.b.get_task_meta(tid)

        # check task meta
        assert mindb.get('result') == {'foo': 'baz'}
        assert mindb.get('task_args') == 'argsrepr'
        assert mindb.get('task_kwargs') == 'kwargsrepr'

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid)
        assert json.loads(tr.task_args) == 'argsrepr'
        assert json.loads(tr.task_kwargs) == 'kwargsrepr'

        # check async_result
        ar = AsyncResult(tid)
        assert ar.args == mindb.get('task_args')
        assert ar.kwargs == mindb.get('task_kwargs')

    def test_secrets__pickle_serialization__protocol_1(self):
        self.app.conf.result_serializer = 'pickle'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid = uuid()
        request = self._create_request(
            task_id=tid,
            name='my_task',
            args=['a', 1, SomeClass(67)],
            kwargs={'c': 6, 'd': 'e', 'f': SomeClass(89)},
            argsrepr='argsrepr',
            kwargsrepr='kwargsrepr',
            task_protocol=1,
        )
        result = {'foo': 'baz'}

        self.b.mark_as_done(tid, result, request=request)

        mindb = self.b.get_task_meta(tid)
        assert mindb.get('result') == {'foo': 'baz'}

        assert mindb.get('task_args')[0] == 'a'
        assert mindb.get('task_args')[1] == 1
        assert mindb.get('task_args')[2].data == 67

        assert mindb.get('task_kwargs')['c'] == 6
        assert mindb.get('task_kwargs')['d'] == 'e'
        assert mindb.get('task_kwargs')['f'].data == 89

        tr = TaskResult.objects.get(task_id=tid)
        task_args = pickle.loads(b64decode(tr.task_args))
        assert task_args[0] == 'a'
        assert task_args[1] == 1
        assert task_args[2].data == 67

        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_kwargs['c'] == 6
        assert task_kwargs['d'] == 'e'
        assert task_kwargs['f'].data == 89

    def test_secrets__json_serialization__protocol_1(self):
        self.app.conf.result_serializer = 'json'
        self.app.conf.accept_content = {'pickle', 'json'}
        self.b = DatabaseBackend(app=self.app)

        tid = uuid()
        request = self._create_request(
            task_id=tid,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
            argsrepr='argsrepr',
            kwargsrepr='kwargsrepr',
            task_protocol=1,
        )
        result = {'foo': 'baz'}

        self.b.mark_as_done(tid, result, request=request)

        mindb = self.b.get_task_meta(tid)

        assert mindb.get('result') == {'foo': 'baz'}
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == ['a', 1, True]
        assert mindb.get('task_kwargs') == {'c': 6, 'd': 'e', 'f': False}

        tr = TaskResult.objects.get(task_id=tid)
        assert json.loads(tr.task_args) == ['a', 1, True]
        assert json.loads(tr.task_kwargs) == {'c': 6, 'd': 'e', 'f': False}

    def test_apply_chord_header_result_arg(self):
        """Test if apply_chord can handle Celery <= 5.1 call signature"""
        gid = uuid()
        tid1 = uuid()
        tid2 = uuid()
        subtasks = [AsyncResult(tid1), AsyncResult(tid2)]
        group = GroupResult(id=gid, results=subtasks)
        # Celery < 5.1
        self.b.apply_chord(group, self.add.s())
        # Celery 5.1
        self.b.apply_chord((uuid(), subtasks), self.add.s())

    def test_on_chord_part_return(self):
        """Test if the ChordCounter is properly decremented and the callback is
        triggered after all chord parts have returned"""
        gid = uuid()
        tid1 = uuid()
        tid2 = uuid()
        subtasks = [AsyncResult(tid1), AsyncResult(tid2)]
        group = GroupResult(id=gid, results=subtasks)
        self.b.apply_chord(group, self.add.s())

        chord_counter = ChordCounter.objects.get(group_id=gid)
        assert chord_counter.count == 2

        request = mock.MagicMock()
        request.id = subtasks[0].id
        request.group = gid
        request.task = "my_task"
        request.args = ["a", 1, "password"]
        request.kwargs = {"c": 3, "d": "e", "password": "password"}
        request.argsrepr = "argsrepr"
        request.kwargsrepr = "kwargsrepr"
        request.hostname = "celery@ip-0-0-0-0"
        request.properties = {"periodic_task_name": "my_periodic_task"}
        request.ignore_result = False
        result = {"foo": "baz"}

        self.b.mark_as_done(tid1, result, request=request)

        chord_counter.refresh_from_db()
        assert chord_counter.count == 1

        self.b.mark_as_done(tid2, result, request=request)

        with pytest.raises(ChordCounter.DoesNotExist):
            ChordCounter.objects.get(group_id=gid)

        request.chord.delay.assert_called_once()

    def test_on_chord_part_return_counter_not_found(self):
        """Test if the chord does not raise an error if the ChordCounter is
        not found

        Basically this covers the case where a chord was created with a version
        <2.0.0 and the update was done before the chord was finished
        """
        request = mock.MagicMock()
        request.id = uuid()
        request.group = uuid()
        self.b.on_chord_part_return(request=request, state=None, result=None)

    def test_callback_failure(self):
        """Test if a failure in the chord callback is properly handled"""
        gid = uuid()
        tid1 = uuid()
        tid2 = uuid()
        cid = uuid()
        subtasks = [AsyncResult(tid1), AsyncResult(tid2)]
        group = GroupResult(id=gid, results=subtasks)
        self.b.apply_chord(group, self.add.s())

        chord_counter = ChordCounter.objects.get(group_id=gid)
        assert chord_counter.count == 2

        request = mock.MagicMock()
        request.id = subtasks[0].id
        request.group = gid
        request.task = "my_task"
        request.args = ["a", 1, "password"]
        request.kwargs = {"c": 3, "d": "e", "password": "password"}
        request.argsrepr = "argsrepr"
        request.kwargsrepr = "kwargsrepr"
        request.hostname = "celery@ip-0-0-0-0"
        request.properties = {"periodic_task_name": "my_periodic_task"}
        request.ignore_result = False
        request.chord.id = cid
        result = {"foo": "baz"}

        # Trigger an exception when the callback is triggered
        request.chord.delay.side_effect = ValueError()

        self.b.mark_as_done(tid1, result, request=request)

        chord_counter.refresh_from_db()
        assert chord_counter.count == 1

        self.b.mark_as_done(tid2, result, request=request)

        with pytest.raises(ChordCounter.DoesNotExist):
            ChordCounter.objects.get(group_id=gid)

        request.chord.delay.assert_called_once()

        assert TaskResult.objects.get(task_id=cid).status == states.FAILURE

    def test_on_chord_part_return_failure(self):
        """Test if a failure in one of the chord header tasks is properly
        handled and the callback was not triggered
        """
        gid = uuid()
        tid1 = uuid()
        tid2 = uuid()
        cid = uuid()
        subtasks = [AsyncResult(tid1), AsyncResult(tid2)]
        group = GroupResult(id=gid, results=subtasks)
        self.b.apply_chord(group, self.add.s())

        chord_counter = ChordCounter.objects.get(group_id=gid)
        assert chord_counter.count == 2

        request = mock.MagicMock()
        request.id = tid1
        request.group = gid
        request.task = "my_task"
        request.args = ["a", 1, "password"]
        request.kwargs = {"c": 3, "d": "e", "password": "password"}
        request.argsrepr = "argsrepr"
        request.kwargsrepr = "kwargsrepr"
        request.hostname = "celery@ip-0-0-0-0"
        request.properties = {"periodic_task_name": "my_periodic_task"}
        request.chord.id = cid
        result = {"foo": "baz"}

        self.b.mark_as_done(tid1, result, request=request)

        chord_counter.refresh_from_db()
        assert chord_counter.count == 1

        request.id = tid2
        self.b.mark_as_failure(tid2, ValueError(), request=request)

        with pytest.raises(ChordCounter.DoesNotExist):
            ChordCounter.objects.get(group_id=gid)

        request.chord.delay.assert_not_called()

    def test_groupresult_save_restore(self):
        """Test if we can save and restore a GroupResult"""
        group_id = uuid()
        results = [AsyncResult(id=uuid())]
        group = GroupResult(id=group_id, results=results)

        group.save(backend=self.b)

        restored_group = self.b.restore_group(group_id=group_id)

        assert restored_group == group

    def test_groupresult_save_restore_nested(self):
        """Test if we can save and restore a nested GroupResult"""
        group_id = uuid()
        async_result = AsyncResult(id=uuid())
        nested_results = [AsyncResult(id=uuid()), AsyncResult(id=uuid())]
        nested_group = GroupResult(id=uuid(), results=nested_results)
        group = GroupResult(id=group_id, results=[nested_group, async_result])

        group.save(backend=self.b)

        restored_group = self.b.restore_group(group_id=group_id)

        assert restored_group == group

    def test_backend_result_extended_is_false(self):
        self.app.conf.result_extended = False
        self.b = DatabaseBackend(app=self.app)
        tid2 = uuid()
        request = self._create_request(
            task_id=tid2,
            name='my_task',
            args=['a', 1, True],
            kwargs={'c': 6, 'd': 'e', 'f': False},
        )
        result = 'foo'

        self.b.mark_as_done(tid2, result, request=request)

        mindb = self.b.get_task_meta(tid2)

        # check meta data
        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') is None
        assert mindb.get('task_args') is None
        assert mindb.get('task_kwargs') is None

        # check task_result object
        tr = TaskResult.objects.get(task_id=tid2)
        assert tr.task_args is None
        assert tr.task_kwargs is None


class DjangoCeleryResultRouter:
    route_app_labels = {"django_celery_results"}

    def db_for_read(self, model, **hints):
        """Route read access to the read-only database"""
        if model._meta.app_label in self.route_app_labels:
            return "read-only"
        return None

    def db_for_write(self, model, **hints):
        """Route write access to the default database"""
        if model._meta.app_label in self.route_app_labels:
            return "default"
        return None


class ChordPartReturnTestCase(TransactionTestCase):
    databases = {"default", "read-only"}

    def setUp(self):
        super().setUp()
        self.app.conf.result_serializer = 'json'
        self.app.conf.result_backend = (
            'django_celery_results.backends:DatabaseBackend')
        self.app.conf.result_extended = True
        self.b = DatabaseBackend(app=self.app)

    def test_on_chord_part_return_multiple_databases(self):
        """
        Test if the ChordCounter is properly decremented and the callback is
        triggered after all chord parts have returned with multiple databases
        """
        with self.settings(DATABASE_ROUTERS=[DjangoCeleryResultRouter()]):
            gid = uuid()
            tid1 = uuid()
            tid2 = uuid()
            subtasks = [AsyncResult(tid1), AsyncResult(tid2)]
            group = GroupResult(id=gid, results=subtasks)

            assert ChordCounter.objects.count() == 0
            assert ChordCounter.objects.using("read-only").count() == 0
            assert ChordCounter.objects.using("default").count() == 0

            self.b.apply_chord(group, self.add.s())

            # Check if the ChordCounter was created in the correct database
            assert ChordCounter.objects.count() == 1
            assert ChordCounter.objects.using("read-only").count() == 1
            assert ChordCounter.objects.using("default").count() == 1

            chord_counter = ChordCounter.objects.get(group_id=gid)
            assert chord_counter.count == 2

            request = mock.MagicMock()
            request.id = subtasks[0].id
            request.group = gid
            request.task = "my_task"
            request.args = ["a", 1, "password"]
            request.kwargs = {"c": 3, "d": "e", "password": "password"}
            request.argsrepr = "argsrepr"
            request.kwargsrepr = "kwargsrepr"
            request.hostname = "celery@ip-0-0-0-0"
            request.properties = {"periodic_task_name": "my_periodic_task"}
            request.ignore_result = False
            result = {"foo": "baz"}

            self.b.mark_as_done(tid1, result, request=request)

            chord_counter.refresh_from_db()
            assert chord_counter.count == 1

            self.b.mark_as_done(tid2, result, request=request)

            with pytest.raises(ChordCounter.DoesNotExist):
                ChordCounter.objects.get(group_id=gid)

            request.chord.delay.assert_called_once()
