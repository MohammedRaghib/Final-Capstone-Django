# Generated by Django 5.1.5 on 2025-02-06 13:28

import datetime
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('task_management', '0027_task_category_alter_task_due_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.RemoveField(
            model_name='task',
            name='category',
        ),
        migrations.AddField(
            model_name='task',
            name='personal',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='personal_account', to='task_management.personal_account'),
        ),
        migrations.AlterField(
            model_name='task',
            name='company',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='tasks', to='task_management.company'),
        ),
        migrations.AlterField(
            model_name='task',
            name='due_date',
            field=models.DateField(default=datetime.datetime(2025, 3, 8, 16, 28, 36, 152181)),
        ),
    ]
