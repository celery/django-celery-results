from django.db import migrations, models


def clear_unfinished_completion_dates(apps, schema_editor):
    """Remove timestamps that represented updates rather than completion."""
    TaskResult = apps.get_model('django_celery_results', 'TaskResult')
    TaskResult.objects.using(schema_editor.connection.alias).exclude(
        status__in=('SUCCESS', 'FAILURE', 'REVOKED'),
    ).update(date_done=None)


def restore_unfinished_dates(apps, schema_editor):
    """Use creation time to satisfy the original non-null constraint."""
    TaskResult = apps.get_model('django_celery_results', 'TaskResult')
    TaskResult.objects.using(schema_editor.connection.alias).filter(
        date_done__isnull=True,
    ).update(date_done=models.F('date_created'))


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0014_alter_taskresult_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='taskresult',
            name='date_done',
            field=models.DateTimeField(
                default=None,
                editable=False,
                null=True,
                verbose_name='Completed DateTime',
                help_text='Datetime field when the task was completed in UTC',
            ),
        ),
        migrations.RunPython(
            clear_unfinished_completion_dates,
            reverse_code=restore_unfinished_dates,
        ),
    ]
