from rest_framework import serializers
from .models import Company, Task, CompanyUser, Comment, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'plan', 'payment_due_date']

class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'created_by', 'company', 'due_date', 'status']

class CompanyUserSerializer(serializers.ModelSerializer):
    user = User
    class Meta:
        model = CompanyUser
        fields = ['id', 'user', 'company', 'role']

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = Comment
        fields = ['id', 'task', 'user', 'text', 'created_at']

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['user', 'company', 'task', 'message', 'is_read', 'created_at']
