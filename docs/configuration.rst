Configuration
=============

These are the available settings that can be configured in your Django
project's settings module by defining a setting with the same name.

.. _settings-task_id_max_length:

* ``DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH`` (Default: ``255``)

  The max length, as an integer, of the ``task_id`` and ``task_name``
  fields on the ``TaskResult`` model. Defaults to 255.

  Also used for the max length of the ``group_id`` fields on the
  ``GroupResult`` and ``ChordCounter`` models.
