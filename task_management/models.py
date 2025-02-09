from django.db import models
from django.contrib.auth import get_user_model
from datetime import timedelta, datetime
User = get_user_model()

class Company(models.Model):
    name = models.CharField(max_length=255)
    plan = models.BooleanField(default=False)
    admin = models.ForeignKey(User, on_delete=models.CASCADE)
    payment_due_date = models.DateField(null=True, blank=True) 
    users = models.ManyToManyField(User, related_name='users', blank=True)
    invited_users = models.ManyToManyField(User, related_name='invitedusers', blank=True)

    def __str__(self):
        return self.name

    def get_user_count(self):
        return self.users.count()

    def is_within_user_limit(self):
        if self.plan:
            return True
        return self.get_user_count() <= 50
    
    def get_admin_email(self):
        return self.admin.email

class Personal_Account(models.Model):
    name = models.CharField(max_length=255)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal')

    def __str__(self):
        return self.name

def default_due_date():
    return datetime.now() + timedelta(days=30)

class Category(models.Model):
    name = models.CharField(max_length=50)
    personal = models.ForeignKey(Personal_Account, on_delete=models.CASCADE, related_name='categories', null=True, blank=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.ManyToManyField(User, related_name='assigned_tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)
    personal = models.ForeignKey(Personal_Account, on_delete=models.CASCADE, related_name='personal_tasks', null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category', null=True, blank=True)
    due_date = models.DateField(default=default_due_date())
    status = models.CharField(max_length=50, choices=[
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ], default='TODO')

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.company and not self.personal:
            raise ValueError("Either 'company' or 'personal' must be set.")
        super(Task, self).save(*args, **kwargs)

Personal_Account.add_to_class('tasks', models.ManyToManyField(Task, related_name='tasks'))

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='task')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def delete_if_read(self):
        if self.is_read:
            self.delete()