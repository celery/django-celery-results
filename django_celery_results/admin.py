"""Result Task Admin interface."""
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import TaskResult

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text  # noqa


class TaskResultAdmin(admin.ModelAdmin):
    """Admin-interface for results of tasks."""

    model = TaskResult
    list_display = ('task_id', 'date_done', 'status')
    readonly_fields = ('date_done', 'result', 'hidden', 'meta')
    fieldsets = (
        (None, {
            'fields': ('task_id', 'status', 'content_type', 'content_encoding', ),
            'classes': ('extrapretty', 'wide')
        }),
        ('Result', {
            'fields': ('result', 'date_done', 'traceback', 'hidden', 'meta'),
            'classes': ('extrapretty', 'wide')
        }),
    )

admin.site.register(TaskResult, TaskResultAdmin)
