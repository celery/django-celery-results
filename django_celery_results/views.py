"""Views."""
from __future__ import absolute_import, unicode_literals

from django.http import JsonResponse

from celery import states
from celery.result import AsyncResult, GroupResult
from celery.utils import get_full_cls_name
from kombu.utils.encoding import safe_repr


def is_task_successful(request, task_id):
    """Return task execution status in JSON format."""
    return JsonResponse({'task': {
        'id': task_id,
        'executed': AsyncResult(task_id).successful(),
    }})


def task_status(request, task_id):
    """Return task status and result in JSON format."""
    result = AsyncResult(task_id)
    state, retval = result.state, result.result
    response_data = {'id': task_id, 'status': state, 'result': retval}
    if state in states.EXCEPTION_STATES:
        traceback = result.traceback
        response_data.update({'result': safe_repr(retval),
                              'exc': get_full_cls_name(retval.__class__),
                              'traceback': traceback})
    return JsonResponse({'task': response_data})

def is_group_successful(request, group_id):
    results = GroupResult.restore(group_id)

    return JsonResponse({
        'group': {
            'id': group_id,
            'results': [
                {'id': task.id, 'executed': task.successful() }
                for task in results
            ] if results else []
        }
    })

def group_status(request, group_id):
    """Return task status and result in JSON format."""
    result = GroupResult.restore(group_id)
    retval = result.result
    response_data = {'id': group_id, 'result': retval}
    return JsonResponse({'task': response_data})
