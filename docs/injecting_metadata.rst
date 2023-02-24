Injecting metadata
===============


To save arbitrary data on the field TaskResult.meta, the Celery Task Request must be manipulated as such:

    .. code-block:: python

        from celery import Celery

        app = Celery('hello', broker='amqp://guest@localhost//')

        @app.task(bind=True)
        def hello(task_instance):
            task_instance.request.meta = {'some_key': 'some_value'}
            task_instance.update_state(
                state='PROGRESS',
                meta='Task current result'
            )
            # If TaskResult is queried from DB at this momento it will yield
            # TaskResult(
            #     result='Task current result',
            #     meta={'some_key': 'some_value'}  # some discrepancies apply as I didn't document the json parse and children data
            # )
            return 'hello world'

        # After task is completed, if TaskResult is queried from DB at this momento it will yield
        # TaskResult(
        #     result='hello world',
        #     meta={'some_key': 'some_value'}  # some discrepancies apply as I didn't document the json parse and children data
        # )

This way, the value of ``task_instance.request.meta`` will be stored on ``TaskResult.meta``.

Note that the `meta` arg in the method `update_state` is not really a metadata and it's not stored on ``TaskResult.meta``.
This arg is used to save the CURRENT result of the task. So it's stored on ``TaskResult.result``.

It works this way because while a task is executing, the `TaskResult` is used really as current task state; holding information, temporarily, until the task completes.
Subsequent calls to `update_state` will update the same `TaskResult`, overwriting what was there previously.
Upon completion of the task, the results of the task are stored in the same TaskResult, overwriting the previous state of the task.
So the return from the function is stored in ``TaskResult.result`` and ``TaskResult.status`` is set to 'SUCCESS' (or 'FAILURE').

