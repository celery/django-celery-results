from __future__ import absolute_import, unicode_literals

import mock
import celery
import json
import pytest
import re
import pickle

from celery import uuid
from celery import states
from celery.app.task import Context
from celery.result import GroupResult, AsyncResult
from celery.utils.serialization import b64decode
from celery.worker.request import Request

from django_celery_results.backends.database import DatabaseBackend
from django_celery_results.models import ChordCounter, TaskResult


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

    def _create_request(self, task_id, name, args, kwargs,
                        argsrepr=None, kwargsrepr=None):
        msg = self.app.amqp.create_task_message(
            task_id=task_id,
            name=name,
            args=args,
            kwargs=kwargs,
            argsrepr=argsrepr,
            kwargsrepr=kwargsrepr,
        )
        headers, properties, body, sent_event = msg
        context = Context(
            headers=headers,
            properties=properties,
            body=body,
            sent_event=sent_event,
        )
        request = Request(context, decoded=True, task=name)
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

        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

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

        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

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

        tr = TaskResult.objects.get(task_id=tid2)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == mindb.get('task_args')
        assert task_kwargs == mindb.get('task_kwargs')

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

        assert mindb.get('result').get('foo') == 'baz'
        assert mindb.get('result').get('bar') is True
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == "['a', 1, True]"
        assert mindb.get('task_kwargs') == "{'c': 6, 'd': 'e', 'f': False}"

        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == "['a', 1, True]"
        assert json.loads(tr.task_kwargs) == "{'c': 6, 'd': 'e', 'f': False}"

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

        assert mindb.get('result') == 'foo'
        assert mindb.get('task_name') == 'my_task'
        assert mindb.get('task_args') == "['a', 1, True]"
        assert mindb.get('task_kwargs') == "{'c': 6, 'd': 'e', 'f': False}"

        tr = TaskResult.objects.get(task_id=tid2)
        assert json.loads(tr.task_args) == "['a', 1, True]"
        assert json.loads(tr.task_kwargs) == "{'c': 6, 'd': 'e', 'f': False}"

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
        assert mindb.get('result') == {'foo': 'baz'}
        assert mindb.get('task_args') == 'argsrepr'
        assert mindb.get('task_kwargs') == 'kwargsrepr'
        assert len(mindb.get('worker')) > 1

        tr = TaskResult.objects.get(task_id=tid)
        task_args = pickle.loads(b64decode(tr.task_args))
        task_kwargs = pickle.loads(b64decode(tr.task_kwargs))
        assert task_args == 'argsrepr'
        assert task_kwargs == 'kwargsrepr'

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
        assert mindb.get('result') == {'foo': 'baz'}
        assert mindb.get('task_args') == 'argsrepr'
        assert mindb.get('task_kwargs') == 'kwargsrepr'

        tr = TaskResult.objects.get(task_id=tid)
        assert json.loads(tr.task_args) == 'argsrepr'
        assert json.loads(tr.task_kwargs) == 'kwargsrepr'

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
        result = {"foo": "baz"}

        self.b.mark_as_done(tid1, result, request=request)

        chord_counter.refresh_from_db()
        assert chord_counter.count == 1

        self.b.mark_as_done(tid2, result, request=request)

        with pytest.raises(ChordCounter.DoesNotExist):
            ChordCounter.objects.get(group_id=gid)

        request.chord.delay.assert_called_once()

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
        """Test if a failure in one of the chord header tasks is properly handled
        and the callback was not triggered
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
