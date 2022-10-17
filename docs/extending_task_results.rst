Extending Task Results
======================

There are situations where you want to extend the Task Results with additional information that will make you able to retrieve information that was important at execution time of the task but not part of the task result itself. For example if you use :pypi:`django-celery-results` to track the task results from a tenant.

To extend the Task Results model follow the next steps:

#. Create a custom model that inherits from the abstract base class `django_celery_results.models.abstract.AbstractTaskResult`:

    .. code-block:: python
            
        from django_celery_results.models.abstract import AbstractTaskResult

        class TaskResult(AbstractTaskResult):
            tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True)

#. Tell Django to use the custom `TaskResult` model by setting the `CELERY_RESULTS_TASKRESULT_MODEL` constant to the path of the custom model.

    .. code-block:: python
        
        CELERY_RESULTS_TASKRESULT_MODEL = 'myapp.TaskResult'

#. Write a function in your Django project's :file:`settings.py` that will consume a `request` and `task_properties` as positional arguments and will return a dictionary with the additional information that you want to store in the your custom `TaskResult` model. The keys of this dictionary will be the fields of the custom model and the values the data you can retrieve from the `request` and/or `task_properties`.

    .. code-block:: python

        def extend_task_props_callback(request, task_properties):
            """Extend task props with custom data from task_kwargs."""
            task_kwargs = getattr(request, "kwargs", None)

            return {"tenant_id": task_kwargs.get("tenant_id", None)}

#. To let :pypi:`django-celery-results` call this function internally you've to set the `CELERY_RESULTS_EXTEND_TASK_PROPS_CALLBACK` constant in your Django project's :file:`settings.py` with the function that you've just created.

        .. code-block:: python
        
        CELERY_RESULTS_EXTEND_TASK_PROPS_CALLBACK = extend_task_props_callback

#. Finally make sure that you're passing the additional information to the celery task when you're calling it.

    .. code-block:: python

        task.apply_async(kwargs={"tenant_id": tenant.id})