"""The Celery events camera."""
from __future__ import absolute_import, unicode_literals

from datetime import timedelta

from celery import states
from celery.events.snapshot import Polaroid
from celery.utils.imports import symbol_by_name
from celery.utils.log import get_logger
from celery.utils.time import maybe_iso8601

from .utils import fromtimestamp, correct_awareness

WORKER_UPDATE_FREQ = 60  # limit worker timestamp write freq.
SUCCESS_STATES = frozenset([states.SUCCESS])

NOT_SAVED_ATTRIBUTES = frozenset(['name', 'args', 'kwargs', 'eta'])

logger = get_logger(__name__)
debug = logger.debug


class Camera(Polaroid):
    """The Celery events Polaroid snapshot camera."""

    clear_after = True
    worker_update_freq = WORKER_UPDATE_FREQ

    def __init__(self, *args, **kwargs):
        super(Camera, self).__init__(*args, **kwargs)
        # Expiry can be timedelta or None for never expire.
        self.app.add_defaults({
            'monitors_expire_success': timedelta(days=1),
            'monitors_expire_error': timedelta(days=3),
            'monitors_expire_pending': timedelta(days=5),
        })

    @property
    def TaskState(self):
        """Return the data model to store task state in."""
        return symbol_by_name('django_celery_monitor.models.TaskState')

    @property
    def WorkerState(self):
        """Return the data model to store worker state in."""
        return symbol_by_name('django_celery_monitor.models.WorkerState')

    def django_setup(self):
        import django
        django.setup()

    def install(self):
        super(Camera, self).install()
        self.django_setup()

    @property
    def expire_task_states(self):
        """Return a twople of Celery task states and expiration timedeltas."""
        return (
            (SUCCESS_STATES, self.app.conf.monitors_expire_success),
            (states.EXCEPTION_STATES, self.app.conf.monitors_expire_error),
            (states.UNREADY_STATES, self.app.conf.monitors_expire_pending),
        )

    def get_heartbeat(self, worker):
        try:
            heartbeat = worker.heartbeats[-1]
        except IndexError:
            return
        return fromtimestamp(heartbeat)

    def handle_worker(self, hostname_worker):
        hostname, worker = hostname_worker
        return self.WorkerState.objects.update_heartbeat(
            hostname,
            heartbeat=self.get_heartbeat(worker),
            update_freq=self.worker_update_freq,
        )

    def handle_task(self, uuid_task, worker=None):
        """Handle snapshotted event."""
        uuid, task = uuid_task
        if task.worker and task.worker.hostname:
            worker = self.handle_worker(
                (task.worker.hostname, task.worker),
            )

        defaults = {
            'name': task.name,
            'args': task.args,
            'kwargs': task.kwargs,
            'eta': correct_awareness(maybe_iso8601(task.eta)),
            'expires': correct_awareness(maybe_iso8601(task.expires)),
            'state': task.state,
            'tstamp': fromtimestamp(task.timestamp),
            'result': task.result or task.exception,
            'traceback': task.traceback,
            'runtime': task.runtime,
            'worker': worker
        }
        # Some fields are only stored in the RECEIVED event,
        # so we should remove these from default values,
        # so that they are not overwritten by subsequent states.
        [defaults.pop(attr, None) for attr in NOT_SAVED_ATTRIBUTES
         if defaults[attr] is None]
        return self.update_task(task.state, task_id=uuid, defaults=defaults)

    def update_task(self, state, task_id, defaults=None):
        defaults = defaults or {}
        if not defaults.get('name'):
            return
        return self.TaskState.objects.update_state(
            state=state,
            task_id=task_id,
            defaults=defaults,
        )

    def on_shutter(self, state):

        def _handle_tasks():
            for i, task in enumerate(state.tasks.items()):
                self.handle_task(task)

        for worker in state.workers.items():
            self.handle_worker(worker)
        _handle_tasks()

    def on_cleanup(self):
        expired = (
            self.TaskState.objects.expire_by_states(states, expires)
            for states, expires in self.expire_task_states
        )
        dirty = sum(item for item in expired if item is not None)
        if dirty:
            debug('Cleanup: Marked %s objects as dirty.', dirty)
            self.TaskState.objects.purge()
            debug('Cleanup: %s objects purged.', dirty)
            return dirty
        return 0
