# Generated by Django 5.1.5 on 2025-01-25 08:48

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0004_alter_notification_company_alter_notification_user_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(default=datetime.datetime(2025, 2, 24, 11, 48, 56, 332641)),
        ),
    ]
