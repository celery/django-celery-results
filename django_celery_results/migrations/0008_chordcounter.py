# Generated by Django 3.0.6 on 2020-05-12 12:05
from __future__ import unicode_literals, absolute_import

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0007_remove_taskresult_hidden'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChordCounter',
            fields=[
                ('id', models.AutoField(
                    auto_created=True,
                    primary_key=True,
                    serialize=False,
                    verbose_name='ID')),
                ('group_id', models.CharField(
                    db_index=True,
                    help_text='Celery ID for the Chord header group',
                    max_length=255,
                    unique=True,
                    verbose_name='Group ID')),
                ('sub_tasks', models.TextField(
                    help_text='JSON serialized list of task result tuples. '
                              'use .group_result() to decode')),
                ('count', models.PositiveIntegerField(
                    help_text='Starts at len(chord header) '
                              'and decrements after each task is finished')),
            ],
        ),
    ]
