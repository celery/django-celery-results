"""Result Task Admin interface."""

from celery import current_app as celery_app
from django.conf import settings
from django.contrib import admin, messages
from django.utils.translation import gettext_lazy as _

try:
    ALLOW_EDITS = settings.DJANGO_CELERY_RESULTS['ALLOW_EDITS']
except (AttributeError, KeyError):
    ALLOW_EDITS = False
    pass

from .models import GroupResult, TaskResult


class TaskResultAdmin(admin.ModelAdmin):
    """Admin-interface for results of tasks."""

    model = TaskResult
    date_hierarchy = 'date_done'
    list_display = ('task_id', 'periodic_task_name', 'task_name', 'date_done',
                    'status', 'worker')
    list_filter = ('status', 'date_done', 'periodic_task_name', 'task_name',
                   'worker')
    readonly_fields = ('date_created', 'date_started', 'date_done',
                       'result', 'meta')
    search_fields = ('task_name', 'task_id', 'status', 'task_args',
                     'task_kwargs')
    fieldsets = (
        (None, {
            'fields': (
                'task_id',
                'task_name',
                'periodic_task_name',
                'status',
                'worker',
                'content_type',
                'content_encoding',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        (_('Parameters'), {
            'fields': (
                'task_args',
                'task_kwargs',
            ),
            'classes': ('extrapretty', 'wide')
        }),
        (_('Result'), {
            'fields': (
                'result',
                'date_created',
                'date_started',
                'date_done',
                'traceback',
                'meta',
            ),
            'classes': ('extrapretty', 'wide')
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if ALLOW_EDITS:
            return self.readonly_fields
        else:
            return list({
                field.name for field in self.opts.local_fields
            })
    
    def terminate_task(self, request, queryset):
        """Terminate selected tasks."""
        for task_result in queryset:
            task_id = task_result.task_id
            try:
                celery_app.control.revoke(task_id, terminate=True)
                self.message_user(request, f'Task {task_id} was terminated successfully.', messages.SUCCESS)
            except Exception as e:
                self.message_user(request, f'Failed to terminate task {task_id}. Error: {e}', messages.ERROR)

    terminate_task.short_description = "Terminate selected tasks"


admin.site.register(TaskResult, TaskResultAdmin)


class GroupResultAdmin(admin.ModelAdmin):
    """Admin-interface for results  of grouped tasks."""

    model = GroupResult
    date_hierarchy = 'date_done'
    list_display = ('group_id', 'date_done')
    list_filter = ('date_done',)
    readonly_fields = ('date_created', 'date_done', 'result')
    search_fields = ('group_id',)


admin.site.register(GroupResult, GroupResultAdmin)
