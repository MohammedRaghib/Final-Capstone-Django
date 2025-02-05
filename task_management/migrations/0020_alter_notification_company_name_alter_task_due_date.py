# Generated by Django 5.1.5 on 2025-02-04 14:37

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0019_alter_notification_user_alter_task_due_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='company_name',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(default=datetime.datetime(2025, 3, 6, 17, 37, 35, 704842)),
        ),
    ]
