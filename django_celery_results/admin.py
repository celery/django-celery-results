"""Result Task Admin interface."""
from __future__ import absolute_import, unicode_literals

from django.contrib import admin

from .models import TaskResult


class TaskResultAdmin(admin.ModelAdmin):
    """Admin-interface for results of tasks."""

    model = TaskResult
    list_display = ('task_name', 'task_id', 'date_done', 'status')
    list_filter = ('status', 'date_done')
    readonly_fields = ('date_done', 'result', 'hidden', 'meta')
    fieldsets = (
        (None, {
            'fields': (
                'task_name',
                'task_id',
                'status',
                'content_type',
                'content_encoding',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        ('Parameters', {
            'fields': (
                'task_args',
                'task_kwargs',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        ('Result', {
            'fields': (
                'result',
                'date_done',
                'traceback',
                'hidden',
                'meta',
            ),
            'classes': ('extrapretty', 'wide')
        }),
    )


admin.site.register(TaskResult, TaskResultAdmin)
