from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('django_celery_results', '0007_remove_taskresult_hidden'),
    ]

    operations = [
        migrations.CreateModel(
            name='GroupResult',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('group_id', models.CharField(max_length=255, unique=True, verbose_name='Group ID')),
                ('date_created', models.DateTimeField(auto_now_add=True, verbose_name='Created DateTime')),
                ('date_done', models.DateTimeField(auto_now=True, verbose_name='Completed DateTime')),
                ('content_type', models.CharField(max_length=128, verbose_name='Result Content Type')),
                ('content_encoding', models.CharField(max_length=64, verbose_name='Result Encoding')),
                ('result', models.TextField(default=None, editable=False, null=True, verbose_name="Result Data")),
            ],
            options={
                'verbose_name': 'group result',
                'verbose_name_plural': 'group results'
            },
        ),
    ]
