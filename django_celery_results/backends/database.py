from __future__ import absolute_import, unicode_literals

import binascii
import json

from celery import maybe_signature
from celery.backends.base import BaseDictBackend
from celery.exceptions import ChordError
from celery.result import allow_join_result
from celery.utils.serialization import b64encode, b64decode
from celery.utils.log import get_logger
from kombu.exceptions import DecodeError
from django.db import transaction

from ..models import TaskResult, ChordCounter


logger = get_logger(__name__)


class DatabaseBackend(BaseDictBackend):
    """The Django database backend, using models to store task state."""

    TaskModel = TaskResult

    subpolling_interval = 0.5

    def _store_result(self, task_id, result, status,
                      traceback=None, request=None, using=None):
        """Store return value and status of an executed task."""
        content_type, content_encoding, result = self.encode_content(result)
        _, _, meta = self.encode_content({
            'children': self.current_task_children(request),
        })

        task_name = getattr(request, 'task', None)
        worker = getattr(request, 'hostname', None)

        # Get input arguments
        if getattr(request, 'argsrepr', None) is not None:
            # task protocol 2
            task_args = request.argsrepr
        else:
            # task protocol 1
            task_args = getattr(request, 'args', None)

        if getattr(request, 'kwargsrepr', None) is not None:
            # task protocol 2
            task_kwargs = request.kwargsrepr
        else:
            # task protocol 1
            task_kwargs = getattr(request, 'kwargs', None)

        # Encode input arguments
        if task_args is not None:
            _, _, task_args = self.encode_content(task_args)

        if task_kwargs is not None:
            _, _, task_kwargs = self.encode_content(task_kwargs)

        self.TaskModel._default_manager.store_result(
            content_type, content_encoding,
            task_id, result, status,
            traceback=traceback,
            meta=meta,
            task_name=task_name,
            task_args=task_args,
            task_kwargs=task_kwargs,
            worker=worker,
            using=using,
        )
        return result

    def _get_task_meta_for(self, task_id):
        """Get task metadata for a task by id."""
        obj = self.TaskModel._default_manager.get_task(task_id)
        res = obj.as_dict()
        meta = self.decode_content(obj, res.pop('meta', None)) or {}
        result = self.decode_content(obj, res.get('result'))

        task_args = res.get('task_args')
        task_kwargs = res.get('task_kwargs')
        try:
            task_args = self.decode_content(obj, task_args)
            task_kwargs = self.decode_content(obj, task_kwargs)
        except (DecodeError, binascii.Error):
            pass

        # the right names are args/kwargs, not task_args/task_kwargs,
        # keep both for backward compatibility
        res.update(
            meta, result=result, task_args=task_args,
            task_kwargs=task_kwargs,
            args=task_args,
            kwargs=task_kwargs,
        )
        return self.meta_from_decoded(res)

    def encode_content(self, data):
        content_type, content_encoding, content = self._encode(data)
        if content_encoding == 'binary':
            content = b64encode(content)
        return content_type, content_encoding, content

    def decode_content(self, obj, content):
        if content:
            if obj.content_encoding == 'binary':
                content = b64decode(content)
            return self.decode(content)

    def _forget(self, task_id):
        try:
            self.TaskModel._default_manager.get(task_id=task_id).delete()
        except self.TaskModel.DoesNotExist:
            pass

    def cleanup(self):
        """Delete expired metadata."""
        self.TaskModel._default_manager.delete_expired(self.expires)

    def apply_chord(self, header_result, body, **kwargs):
        """Add a ChordCounter with the expected number of results"""
        results = [r.as_tuple() for r in header_result]
        data = json.dumps(results)
        ChordCounter.objects.create(
            group_id=header_result.id, sub_tasks=data, count=len(results)
        )

    def on_chord_part_return(self, request, state, result, **kwargs):
        """Called on finishing each part of a Chord header"""
        tid, gid = request.id, request.group
        if not gid or not tid:
            return
        call_callback = False
        with transaction.atomic():
            # We need to know if `count` hits 0.
            # wrap the update in a transaction
            # with a `select_for_update` lock to prevent race conditions.
            # SELECT FOR UPDATE is not supported on all databases
            chord_counter = (
                ChordCounter.objects.select_for_update()
                .get(group_id=gid)
            )
            chord_counter.count -= 1
            if chord_counter.count != 0:
                chord_counter.save()
            else:
                # Last task in the chord header has finished
                call_callback = True
                chord_counter.delete()

        if call_callback:
            deps = chord_counter.group_result(app=self.app)
            if deps.ready():
                callback = maybe_signature(request.chord, app=self.app)
                trigger_callback(
                    app=self.app,
                    callback=callback,
                    group_result=deps
                )


def trigger_callback(app, callback, group_result):
    """Add the callback to the queue or mark the callback as failed

    Implementation borrowed from `celery.app.builtins.unlock_chord`
    """
    j = (
        group_result.join_native
        if group_result.supports_native_join
        else group_result.join
    )

    try:
        with allow_join_result():
            ret = j(timeout=app.conf.result_chord_join_timeout, propagate=True)
    except Exception as exc:  # pylint: disable=broad-except
        try:
            culprit = next(group_result._failed_join_report())
            reason = "Dependency {0.id} raised {1!r}".format(culprit, exc)
        except StopIteration:
            reason = repr(exc)
        logger.exception("Chord %r raised: %r", group_result.id, exc)
        app.backend.chord_error_from_stack(callback, ChordError(reason))
    else:
        try:
            callback.delay(ret)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Chord %r raised: %r", group_result.id, exc)
            app.backend.chord_error_from_stack(
                callback, exc=ChordError("Callback error: {0!r}".format(exc))
            )
