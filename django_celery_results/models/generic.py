"""Database models."""

import json

from celery.result import GroupResult as CeleryGroupResult
from celery.result import result_from_tuple
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from django_celery_results.models.abstract import (
    AbstractGroupResult,
    AbstractTaskResult,
)


class TaskResult(AbstractTaskResult):
    """Task result/status."""

    class Meta(AbstractTaskResult.Meta):
        """Table information."""

        abstract = False


class ChordCounter(models.Model):
    """Chord synchronisation."""

    group_id = models.CharField(
        max_length=getattr(
            settings,
            "DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH",
            255),
        unique=True,
        verbose_name=_("Group ID"),
        help_text=_("Celery ID for the Chord header group"),
    )
    sub_tasks = models.TextField(
        help_text=_(
            "JSON serialized list of task result tuples. "
            "use .group_result() to decode"
        )
    )
    count = models.PositiveIntegerField(
        help_text=_(
            "Starts at len(chord header) and decrements after each task is "
            "finished"
        )
    )

    def group_result(self, app=None):
        """Return the GroupResult of self.

        Arguments:
        ---------
            app (Celery): app instance to create the GroupResult with.

        """
        return CeleryGroupResult(
            self.group_id,
            [result_from_tuple(r, app=app)
             for r in json.loads(self.sub_tasks)],
            app=app
        )


class GroupResult(AbstractGroupResult):
    """Task Group result/status."""

    class Meta(AbstractGroupResult.Meta):
        """Table information."""

        abstract = False
