from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import datetime, timedelta
from .utils import fetch_all_data
from .models import (
    Company,
    Task,
    Notification,
    Comment,
)
from .serializers import (
    CompanySerializer,
    CommentSerializer,
    TaskSerializer,
    NotificationSerializer,
    OverallAdminCompanySerializer
)
from custom_user_model.serializer import CustomUserSerializer
User = get_user_model()

def default_due_date():
    return datetime.now() + timedelta(days=30)

@api_view(['POST', 'GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_view(request, companyid=None):
    if request.method == 'GET':
        try:
            company = Company.objects.get(id=companyid)
            company_tasks = company.tasks.prefetch_related('assigned_to').all()
            company_notifications = company.company.all()
            company_users = company.users.all()
            all_users = User.objects.exclude(id__in=company_users).exclude(id=company.admin.id)

            company_data = CompanySerializer(company).data
            company_data['tasks'] = TaskSerializer(company_tasks, many=True).data
            company_data['noncompanyusers'] = CustomUserSerializer(all_users, many=True).data
            company_data['notifications'] = NotificationSerializer(company_notifications, many=True).data
            company_data['detail'] = 'Company details fetched'

            return Response(company_data, status=status.HTTP_200_OK)
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
    from rest_framework import status
    if request.method == 'GET':
        if taskid: 
            try:
                task = Task.objects.prefetch_related('comments').get(id=taskid, company__id=companyid)
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
            task_id = taskid
            task = Task.objects.get(id=task_id, company__id=companyid)
            assigned_ids = request.data.get('assigned_to')

            if assigned_ids is not None:
                assigned_to = User.objects.filter(id__in=assigned_ids)
                task.assigned_to.set(assigned_to)
            title = request.data.get('title')
            description = request.data.get('description')
            due_date = request.data.get('due_date')
            task_status = request.data.get('status')

            if title:
                task.title = title
            if description:
                task.description = description
            if due_date:
                task.due_date = due_date
            if task_status:
                task.status = task_status
            task.save()

            task_data = TaskSerializer(task).data
            return Response({'detail': 'Task updated', 'task': task_data}, status=200)
        except ObjectDoesNotExist as e:
            print(e)
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    elif request.method == 'DELETE':
        try:
            task_id = taskid
            task = Task.objects.get(id=task_id, company__id=companyid)
            task.delete()
            return Response({'detail': 'Task deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
@api_view(['POST', 'GET', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_user_view(request, companyid=None, userid=None):
    if request.method == 'GET':
        try:
            company = Company.objects.get(id=companyid)
            users_data = CustomUserSerializer(company.users.all(), many=True).data
            return Response({'detail': 'Company users fetched', 'users': users_data}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        try:
            user = User.objects.get(id=request.data.get('user_id'))
            company = Company.objects.get(id=companyid)
            
            company.users.add(user)

            users_data = CustomUserSerializer(company.users.all(), many=True).data
            return Response({'detail': 'User added to company', 'users': users_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company or User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        try:
            user = User.objects.get(id=userid)
            company = Company.objects.get(id=companyid)

            if company.admin == user:
                return Response({'detail': 'Cannot remove the admin from the company'}, status=status.HTTP_400_BAD_REQUEST)
            
            company.users.remove(user)

            users_data = CustomUserSerializer(company.users.all(), many=True).data
            return Response({'detail': 'User removed from company', 'users': users_data}, status=status.HTTP_204_NO_CONTENT)
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
                notification = Notification.objects.prefetch_related('company').get(id=notificationid, user__id=userid)
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
            print(e)
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

    admin_companies = Company.objects.filter(admin=user).first()

    user_companies = Company.objects.filter(users=user).first()

    user_info = {
        'companies': [],
        'detail': ''
    }

    if admin_companies:
        user_info['companies'] = CompanySerializer(admin_companies).data
        user_info['detail'] = 'Admin, User companies found'
    elif user_companies:
        companies = CompanySerializer(user_companies).data
        user_info['companies'] = companies
        user_info['detail'] = 'Employee, User companies found'
    else:
        user_info['companies'] = []
        user_info['detail'] = 'No companies found for the user'
        # return Response(status=status.HTTP_204_NO_CONTENT)

    return Response(user_info, status=status.HTTP_200_OK)

@api_view(['GET'])
def get_tasks_assigned_to_user(request, userid):
    tasks = Task.objects.filter(assigned_to=userid)
    if tasks.exists():
        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)
    return Response({"error": "No tasks found for this user."}, status=status.HTTP_204_NO_CONTENT)

@api_view(['POST', 'DELETE'])
def Accept_or_decline_invite(request, userid=None, companyid=None):
    if request.method == 'POST':
        if not companyid:
            return Response({'detail': 'Company ID must be provided'}, status=status.HTTP_404_NOT_FOUND)
        elif not userid:
            return Response({'detail': 'User ID must be provided'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user = User.objects.get(id=userid)
            company = Company.objects.get(id=companyid)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        other_invite_notifications = Notification.objects.filter(user=userid)
        other_invite_notifications.delete()

        company.users.add(user)
        company.invited_users.remove(user)

        return Response({'detail': 'User added to the company'}, status=status.HTTP_200_OK)

    elif request.method == 'DELETE':
        if not companyid:
            return Response({'detail': 'Company ID must be provided'}, status=status.HTTP_404_NOT_FOUND)
        elif not userid:
            return Response({'detail': 'User ID must be provided'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            user = User.objects.get(id=userid)
            company = Company.objects.get(id=companyid)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Company.DoesNotExist:
            return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

        invite_notification = Notification.objects.filter(user=user, company=company).first()
        if invite_notification:
            invite_notification.delete()
        company.invited_users.remove(user)
        company_notification = Notification.objects.create(
            user=company.admin, 
            message=f'User: {user.username} declined offer to join'
        )

        return Response({'detail': 'Company offer declined'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def fetch_data(request):
    if request.method == 'GET':
        try:
            companies = Company.objects.all()
            all_companies_data = []

            for company in companies:
                company_tasks = company.tasks.prefetch_related('assigned_to').all()
                company_notifications = company.company.all()
                company_users = company.users.all()
                all_users = User.objects.exclude(id__in=company_users).exclude(id=company.admin.id)

                company_data = CompanySerializer(company).data
                company_data['tasks'] = TaskSerializer(company_tasks, many=True).data
                company_data['noncompanyusers'] = CustomUserSerializer(all_users, many=True).data
                company_data['notifications'] = NotificationSerializer(company_notifications, many=True).data
                company_data['admin_name'] = company.get_admin_email()

                all_companies_data.append(company_data)

            return Response(all_companies_data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'No company found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)