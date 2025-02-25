# Generated by Django 5.1.5 on 2025-02-06 17:42

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0032_alter_task_due_date_alter_task_personal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='task',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='task', to='task_management.task'),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(default=datetime.datetime(2025, 3, 8, 20, 42, 26, 490042)),
        ),
    ]
