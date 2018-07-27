"""Database models."""
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils.translation import ugettext_lazy as _

from celery import states
from celery.five import python_2_unicode_compatible

from . import managers
from .picklefield import PickledObjectField

ALL_STATES = sorted(states.ALL_STATES)
TASK_STATE_CHOICES = sorted(zip(ALL_STATES, ALL_STATES))


@python_2_unicode_compatible
class TaskResult(models.Model):
    """Task result/status."""

    task_id = models.CharField(
        _('task id'),
        max_length=255, unique=True,
    )
    status = models.CharField(
        _('state'),
        max_length=50, default=states.PENDING,
        choices=TASK_STATE_CHOICES,
    )
    content_type = models.CharField(
        _('content type'), max_length=128,
    )
    content_encoding = models.CharField(
        _('content encoding'), max_length=64,
    )
    result = models.TextField(null=True, default=None, editable=False)
    date_done = models.DateTimeField(_('done at'), auto_now=True)
    traceback = models.TextField(_('traceback'), blank=True, null=True)
    hidden = models.BooleanField(editable=False, default=False, db_index=True)
    meta = models.TextField(null=True, default=None, editable=False)

    objects = managers.TaskResultManager()

    class Meta:
        """Table information."""

        verbose_name = _('task result')
        verbose_name_plural = _('task results')

    def as_dict(self):
        return {
            'task_id': self.task_id,
            'status': self.status,
            'result': self.result,
            'date_done': self.date_done,
            'traceback': self.traceback,
            'meta': self.meta,
        }

    def __str__(self):
        return '<Task: {0.task_id} ({0.status})>'.format(self)

@python_2_unicode_compatible
class TaskSetMeta(models.Model):
    """TaskSet result"""
    taskset_id = models.CharField(_('group id'), max_length=255, unique=True)
    result = PickledObjectField()
    date_done = models.DateTimeField(_('created at'), auto_now=True)
    hidden = models.BooleanField(editable=False, default=False, db_index=True)

    objects = managers.TaskSetManager()

    class Meta:
        """Model meta-data."""
        verbose_name = _('saved group result')
        verbose_name_plural = _('saved group results')
        db_table = 'celery_tasksetmeta'

    def to_dict(self):
        return {'taskset_id': self.taskset_id,
                'result': self.result,
                'date_done': self.date_done}

    def __str__(self):
        return '<TaskSet: {0.taskset_id}>'.format(self)
