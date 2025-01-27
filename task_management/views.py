from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import datetime, timedelta
from .models import (
    Company,
    Task,
    Notification,
    CompanyUser,
    Comment,
)
from .serializers import (
    CompanySerializer,
    CommentSerializer,
    CompanyUserSerializer,
    TaskSerializer,
    NotificationSerializer,
)
User = get_user_model

def default_due_date():
    return datetime.now() + timedelta(days=30)

@api_view(['POST', 'GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_view(request, companyid=None):
    if request.method == 'GET':
        try:
            company = Company.objects.get(id=companyid)
            company_tasks = company.tasks.all()
            company_notifications = company.notifications.all()
            company_users = company.users.all()

            company_data = CompanySerializer(company).data
            company_data['tasks'] = TaskSerializer(company_tasks, many=True).data
            company_data['users'] = CompanyUserSerializer(company_users, many=True).data
            company_data['notifications'] = NotificationSerializer(company_notifications, many=True).data

            return Response({'detail': 'Company details fetched', 'company': company_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'No company found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'POST':
        if not request.data.get('name'):
            return Response({'detail': 'Company name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if Company.objects.filter(name=request.data.get('name')).exists():
            return Response({'detail': 'Organization already exists'}, status=status.HTTP_409_CONFLICT)
        else:
            try:
                name = request.data.get('name')
                admin = request.user
                company = Company.objects.create(name=name, admin=admin)
                company_data = CompanySerializer(company).data
                return Response({'detail': 'Organization created', 'company': company_data}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    elif request.method == 'PUT':
        try:
            company = Company.objects.get(id=companyid)
            name = request.data.get('name')
            if name:
                company.name = name
            company.save()
            company_data = CompanySerializer(company).data
            return Response({'detail': 'Company updated', 'company': company_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'No company found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        try:
            company = Company.objects.get(id=companyid)
            company.delete()
            return Response({'detail': 'Company deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'No company found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        return Response({'detail':'No method found'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)
        
@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def task_view(request, companyid=None, taskid=None):
    if request.method == 'GET':
        if taskid: 
            try:
                task = Task.objects.get(id=taskid, company__id=companyid)
                task_data = TaskSerializer(task).data
                return Response({'detail': 'Task fetched', 'task': task_data}, status=status.HTTP_200_OK)
            except Task.DoesNotExist:
                return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        else:  
            try:
                tasks = Task.objects.filter(company__id=companyid)
                tasks_data = TaskSerializer(tasks, many=True).data
                return Response({'detail': 'Tasks fetched', 'tasks': tasks_data}, status=status.HTTP_200_OK)
            except Company.DoesNotExist:
                return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        try:
            title = request.data.get('title')
            description = request.data.get('description')
            assigned_to = User.objects.filter(id__in=request.data.get('assigned_to', []))
            company = Company.objects.get(id=companyid)
            due_date = request.data.get('due_date')

            task = Task.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                company=company,
                due_date=due_date or default_due_date()
            )
            task.assigned_to.add(*assigned_to)

            task_data = TaskSerializer(task).data
            return Response({'detail': 'Task created', 'task': task_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company or User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    elif request.method == 'PUT':
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id, company__id=companyid)

            title = request.data.get('title')
            description = request.data.get('description')
            assigned_to = User.objects.filter(id__in=request.data.get('assigned_to'))
            due_date = request.data.get('due_date')
            status = request.data.get('status')

            if title:
                task.title = title
            if description:
                task.description = description
            if due_date:
                task.due_date = due_date
            if status:
                task.status = status

            task.assigned_to.set(assigned_to)
            task.save()

            task_data = TaskSerializer(task).data
            return Response({'detail': 'Task updated', 'task': task_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        try:
            task_id = request.data.get('task_id')
            task = Task.objects.get(id=task_id, company__id=companyid)
            task.delete()
            return Response({'detail': 'Task deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST', 'GET'])
@permission_classes([IsAuthenticated])
def company_user_view(request, companyid=None):
    if request.method == 'GET':
        try:
            company_users = CompanyUser.objects.filter(company__id=companyid)
            users_data = CompanyUserSerializer(company_users, many=True).data
            return Response({'detail': 'Company users fetched', 'users': users_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        try:
            user = User.objects.get(id=request.data.get('user_id'))
            company = Company.objects.get(id=companyid)
            role = request.data.get('role', 'USER')

            company_user = CompanyUser.objects.create(user=user, company=company, role=role)
            user_data = CompanyUserSerializer(company_user).data
            return Response({'detail': 'User assigned to company', 'user': user_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company or User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def comment_view(request, taskid=None):
    if request.method == 'GET':
        try:
            comments = Comment.objects.filter(task__id=taskid)
            comments_data = CommentSerializer(comments, many=True).data
            return Response({'detail': 'Comments fetched', 'comments': comments_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        try:
            user = request.user
            task = Task.objects.get(id=taskid)
            text = request.data.get('text')

            comment = Comment.objects.create(user=user, task=task, text=text)
            comment_data = CommentSerializer(comment).data
            return Response({'detail': 'Comment created', 'comment': comment_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            comment_id = request.data.get('comment_id')
            comment = Comment.objects.get(id=comment_id, task__id=taskid)
            comment.delete()
            return Response({'detail': 'Comment deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Comment not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def notification_view(request, userid, notificationid=None):
    if request.method == 'GET':
        if notificationid:
            try:
                notification = Notification.objects.get(id=notificationid, user__id=userid)
                notification_data = NotificationSerializer(notification).data
                return Response({'detail': 'Notification fetched', 'notification': notification_data}, status=status.HTTP_200_OK)
            except Notification.DoesNotExist:
                return Response({'detail': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            notifications = Notification.objects.filter(user__id=userid)
            notifications_data = NotificationSerializer(notifications, many=True).data
            return Response({'detail': 'Notifications fetched', 'notifications': notifications_data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        try:
            user = User.objects.get(id=userid)
            message = request.data.get('message')
            company_id = request.data.get('company_id')
            task_id = request.data.get('task_id')

            company = Company.objects.get(id=company_id) if company_id else None
            task = Task.objects.get(id=task_id) if task_id else None

            notification = Notification.objects.create(user=user, company=company, task=task, message=message)
            notification_data = NotificationSerializer(notification).data
            return Response({'detail': 'Notification created', 'notification': notification_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'User, Company, or Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            notification_id = request.data.get('notification_id')
            notification = Notification.objects.get(id=notification_id, user__id=userid)
            notification.delete()
            return Response({'detail': 'Notification deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_companies(request):
    if not request.user.is_authenticated:
        return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

    user = request.user

    admin_companies = Company.objects.filter(admin=user)

    user_companies = CompanyUser.objects.filter(user=user)

    user_info = {
        'companies': [],
        'detail': ''
    }

    if admin_companies.exists():
        user_info['companies'] = [{
            'company_id': company.id,
            'company_name': company.name
        } for company in admin_companies]
        user_info['detail'] = 'Admin, User companies found'
    elif user_companies.exists():
        companies = [{
            'company_id': company.company.id,
            'company_name': company.company.name  
        } for company in user_companies]
        user_info['companies'] = companies
        user_info['detail'] = 'Employee, User companies found'
    else:
        user_info['companies'] = []
        user_info['detail'] = 'No companies found for the user'

    return Response(user_info, status=status.HTTP_200_OK)