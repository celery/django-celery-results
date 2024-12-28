"""Database models."""

from django_celery_results.models.abstract import (
    AbstractChordCounter,
    AbstractGroupResult,
    AbstractTaskResult,
)


class TaskResult(AbstractTaskResult):
    """Task result/status."""

    class Meta(AbstractTaskResult.Meta):
        """Table information."""

        abstract = False
        app_label = "django_celery_results"


class ChordCounter(AbstractChordCounter):
    """Chord synchronisation."""

    class Meta(AbstractChordCounter.Meta):
        """Table information."""

        abstract = False
        app_label = "django_celery_results"


class GroupResult(AbstractGroupResult):
    """Task Group result/status."""

    class Meta(AbstractGroupResult.Meta):
        """Table information."""

        abstract = False
        app_label = "django_celery_results"
