from __future__ import absolute_import, unicode_literals

from base64 import b64encode, b64decode

from celery.backends.base import BaseDictBackend

from ..models import TaskResult, TaskSetMeta


class DatabaseBackend(BaseDictBackend):
    """The Django database backend, using models to store task state."""

    TaskModel = TaskResult
    TaskSetModel = TaskSetMeta

    subpolling_interval = 0.5

    def _store_result(self, task_id, result, status,
                      traceback=None, request=None, using=None):
        """Store return value and status of an executed task."""
        content_type, content_encoding, result = self.encode_content(result)
        _, _, meta = self.encode_content({
            'children': self.current_task_children(request),
        })

        task_name = getattr(request, 'task', None) if request else None
        task_args = getattr(request,
                            'argsrepr', getattr(request, 'args', None))
        task_kwargs = getattr(request,
                              'kwargsrepr', getattr(request, 'kwargs', None))
        worker = getattr(request, 'hostname', None)

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

    def _save_group(self, group_id, result):
        """Store the result of an executed group."""
        self.TaskSetModel._default_manager.store_result(group_id, result)
        return result

    def _get_task_meta_for(self, task_id):
        """Get task metadata for a task by id."""
        obj = self.TaskModel._default_manager.get_task(task_id)
        res = obj.as_dict()
        meta = self.decode_content(obj, res.pop('meta', None)) or {}
        res.update(meta,
                   result=self.decode_content(obj, res.get('result')))
        return self.meta_from_decoded(res)

    def _restore_group(self, group_id):
        """Get group metadata for a group by id."""
        meta = self.TaskSetModel._default_manager.restore_taskset(group_id)
        if meta:
            return meta.to_dict()

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

    def _delete_group(self, group_id):
        self.TaskSetModel._default_manager.delete_taskset(group_id)

    def _forget(self, task_id):
        try:
            self.TaskModel._default_manager.get(task_id=task_id).delete()
        except self.TaskModel.DoesNotExist:
            pass

    def cleanup(self):
        """Delete expired metadata."""
        self.TaskModel._default_manager.delete_expired(self.expires)
        self.TaskSetModel._default_manager.delete_expired(self.expires)
