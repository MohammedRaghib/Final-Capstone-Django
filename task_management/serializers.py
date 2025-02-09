from rest_framework import serializers
from .models import Company, Task, Comment, Notification, Category, Personal_Account
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

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class TaskSerializer(serializers.ModelSerializer):
    comments = CommentSerializer(many=True, read_only=True)
    category = CategorySerializer()
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'assigned_to', 'created_by', 'company', 'personal', 'category', 'due_date', 'status', 'comments']


class NotificationSerializer(serializers.ModelSerializer):
    company = CompanySerializer()
    class Meta:
        model = Notification
        fields = ['id', 'user', 'company','task', 'message', 'is_read', 'created_at']

class OverallAdminCompanySerializer(serializers.ModelSerializer):
    tasks = TaskSerializer(many=True)
    users = CustomUserSerializer(many=True)
    invited_users = CustomUserSerializer(many=True)
    company = NotificationSerializer(many=True)

    class Meta:
        model = Company
        fields = '__all__'

class Personal_AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Personal_Account
        fields = '__all__'

