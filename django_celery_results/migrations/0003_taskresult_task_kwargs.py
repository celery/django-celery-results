# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-27 10:11
from __future__ import absolute_import, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('celery_results', '0002_taskresult_task_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskresult',
            name='task_kwargs',
            field=models.TextField(null=True, verbose_name='task_kwargs'),
        ),
    ]