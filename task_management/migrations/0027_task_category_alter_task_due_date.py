# Generated by Django 5.1.5 on 2025-02-06 13:07

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0026_personal_account_tasks_alter_task_due_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='category',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(default=datetime.datetime(2025, 3, 8, 16, 7, 13, 215226)),
        ),
    ]
