Injecting metadata
===============

To save arbitrary data on the field TaskResult.meta, the Celery Task Request must be manipulated as such:

    .. code-block:: python

        from celery import Celery

        app = Celery('hello', broker='amqp://guest@localhost//')

        @app.task(bind=True)
        def hello(task_instance):
            task_instance.request.meta = {'some_key': 'some_value'}
            return 'hello world'

This way, the value of ``task_instance.request.meta`` will be stored on ``TaskResult.meta``.
