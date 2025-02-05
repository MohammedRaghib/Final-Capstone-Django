from rest_framework import serializers
from .models import Company, Task, Comment, Notification
from django.contrib.auth import get_user_model
from custom_user_model.serializer import CustomUserSerializer
User = get_user_model()

class CompanySerializer(serializers.ModelSerializer):
    users = CustomUserSerializer(many=True)
    class Meta:
        model = Company
        fields = '__all__'

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    class Meta:
        model = Comment
        fields = ['id', 'task', 'user', 'text', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'created_by', 'company', 'due_date', 'status', 'comments']


class NotificationSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    class Meta:
        model = Notification
        fields = ['id', 'user', 'company', 'company_name','task', 'message', 'is_read', 'created_at']

class OverallAdminCompanySerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True)
    users = CustomUserSerializer(many=True)
    invited_users = CustomUserSerializer(many=True)
    company = NotificationSerializer(many=True)

    class Meta:
        model = Company
        fields = '__all__'