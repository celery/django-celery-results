from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0011_taskresult_periodic_task_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='chordcounter',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID',
            ),
        ),
        migrations.AlterField(
            model_name='groupresult',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID',
            ),
        ),
        migrations.AlterField(
            model_name='taskresult',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID',
            ),
        ),
    ]
