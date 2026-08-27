from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("django_celery_results", "0014_alter_taskresult_status"),
    ]

    operations = [
        migrations.AddField(
            model_name="taskresult",
            name="queue",
            field=models.CharField(
                default=None,
                help_text="Queue the task was sent to",
                max_length=255,
                null=True,
                verbose_name="Queue",
            ),
        ),
        migrations.AddField(
            model_name="taskresult",
            name="retries",
            field=models.IntegerField(
                default=None,
                help_text="Number of times the task has been retried",
                null=True,
                verbose_name="Retries",
            ),
        ),
    ]
