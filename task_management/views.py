from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from datetime import datetime, timedelta
import time
from .models import (
    Company,
    Task,
    Notification,
    Comment,
    Personal_Account,
    Category
)
from .serializers import (
    CompanySerializer,
    CommentSerializer,
    TaskSerializer,
    NotificationSerializer,
    OverallAdminCompanySerializer,
    Personal_AccountSerializer,
    CategorySerializer,
)
from custom_user_model.serializer import CustomUserSerializer
User = get_user_model()

def default_due_date():
    return datetime.now() + timedelta(days=30)

@api_view(['POST', 'GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def company_view(request, companyid=None):
    if request.method == 'GET':
        def create_notification(task, entity, entity_type):
            if not Notification.objects.filter(task=task.id).exists():
                message = f'{task.title} is due in one day'
                if entity_type == 'company':
                    Notification.objects.create(company=entity, message=message)
                elif entity_type == 'personal':
                    Notification.objects.create(personal=entity, message=message)
        try:
            company = Company.objects.filter(id=companyid).first()
            if not company:
                raise ObjectDoesNotExist("Company not found")

            company_tasks = company.tasks.prefetch_related('assigned_to').all()
            current_date = datetime.now().date()

            for task in company_tasks:
                if task.due_date == current_date + timedelta(days=1) and task.status != 'DONE':
                    create_notification(task, companyid, 'company')

            company_notifications = company.notifications.all()
            company_users = company.users.all()
            invited_users = company.invited_users.all()
            all_users = User.objects.exclude(id__in=company_users).exclude(id__in=invited_users).exclude(id=company.admin.id)

            company_data = CompanySerializer(company).data
            company_data['tasks'] = TaskSerializer(company_tasks, many=True).data
            company_data['noncompanyusers'] = CustomUserSerializer(all_users, many=True).data
            company_data['notifications'] = NotificationSerializer(company_notifications, many=True).data
            company_data['detail'] = 'Company details fetched'
        except ObjectDoesNotExist as e:
            print('No company found', e)
            company_data = []
        try:
            personal = Personal_Account.objects.filter(admin=request.user).first()
            current_date = datetime.now().date()
            if personal:
                personal_tasks = personal.personal_tasks.all()
                for task in personal_tasks:
                    if task.due_date == current_date + timedelta(days=1) and task.status != 'DONE':
                        create_notification(task, personal, 'personal')

                personal_data = {
                    "id": personal.id,
                    "name": personal.name,
                    "admin": CustomUserSerializer(personal.admin).data,
                    "tasks": TaskSerializer(personal_tasks, many=True).data,
                    'detail': 'Personal account found'
                }
            else:
                personal_data = {'detail': 'No personal account found'}
        except ObjectDoesNotExist as e:
            print('No company or personal found', e)
            return Response({'detail': 'No company found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"company": company_data, "personal": personal_data}, status=status.HTTP_200_OK)

    elif request.method == 'POST':
        if not request.data.get('name'):
            return Response({'detail': 'Company name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if Company.objects.filter(name=request.data.get('name')).exists():
            return Response({'detail': 'Organization already exists'}, status=status.HTTP_409_CONFLICT)
        else:
            try:
                name = request.data.get('name')
                admin_id = request.data.get('admin')
                if admin_id:
                    admin = User.objects.get(id=admin_id)
                else:
                    admin = request.user
                company = Company.objects.create(name=name, admin=admin)
                company_data = CompanySerializer(company).data
                all_notifications = Notification.objects.filter(user=admin)
                all_notifications.delete()
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
            print(assigned_to)
            for assignee in assigned_to:
                print(f"Assigning to: {assignee}")
                if assignee:
                    try:
                        notification_user = Notification.objects.create(
                            user=assignee, 
                            message=f'You have been assigned the task "{task.title}"'
                        )
                        print(f"Notification created for user: {assignee}")
                    except Exception as e:
                        print(f"Error creating notification for user {assignee}: {e}")
                else:
                    print('No valid assignee found')

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
            tasks = Task.objects.filter(assigned_to=user)

            for task in tasks:
                task.assigned_to.remove(user)
            notification_removed_user = Notification.objects.create(user=company.admin,company=company, message=f'{user.username} left or was removed from company')

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
            personal_id = request.data.get('personal_id')
            task_id = request.data.get('task_id')

            company = Company.objects.get(id=company_id) if company_id else None
            personal = Personal_Account.objects.get(id=personal_id) if personal_id else None
            task = Task.objects.get(id=task_id) if task_id else None
            if company and task:
                notification = Notification.objects.create(user=user, task=task, message=message, company= company)
            elif personal and task:
                notification = Notification.objects.create(user=user, task=task, message=message)
            else:
                notification = Notification.objects.create(user=user, message=message)
            if message == 'Invite' and company:
                company.invited_users.add(user)
            
            notification_data = NotificationSerializer(notification).data
            return Response({'detail': 'Notification created', 'notification': notification_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'User, Company, or Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        try:
            notification = Notification.objects.get(id=notificationid, user__id=userid)
            notification.delete()
            return Response({'detail': 'Notification deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_user_companies(request):
    try:
        if not request.user.is_authenticated:
            return Response({'detail': 'Authentication required.'}, status=status.HTTP_401_UNAUTHORIZED)

        user = request.user

        admin_companies = Company.objects.filter(admin=user).first()

        user_companies = Company.objects.filter(users=user).first()

        personal_company = Personal_Account.objects.filter(admin=user).first()

        user_info = {
            'company': [],
            'detail': '',
            'personal': [],
        }

        if admin_companies:
            user_info['company'] = CompanySerializer(admin_companies).data
            user_info['detail'] = 'Admin, User companies found'
        elif user_companies:
            companies = CompanySerializer(user_companies).data
            user_info['company'] = companies
            user_info['detail'] = 'Employee, User companies found'
        else:
            user_info['company'] = []
            user_info['detail'] = 'No companies found for the user'
            # return Response(status=status.HTTP_204_NO_CONTENT)

        if personal_company:
            personal = Personal_AccountSerializer(personal_company).data
            user_info['personal'] = personal

        return Response(user_info, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"Error fetching user companies: {e}")
        return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        company_notification = Notification.objects.create(
            company=company,
            user=company.admin, 
            message=f'User: {user.username} approved offer to join'
        )

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
            company=company,
            user=company.admin, 
            message=f'User: {user.username} declined offer to join'
        )

        return Response({'detail': 'Company offer declined'}, status=status.HTTP_200_OK)

@api_view(['GET'])
def fetch_data(request):
    if request.method == 'GET':
        try:
            companies = Company.objects.all()
            personal_accounts = Personal_Account.objects.all()
            all_personal_accounts = []
            all_companies_data = []

            for company in companies:
                company_tasks = company.tasks.prefetch_related('assigned_to').all()
                current_date = datetime.now().date()
                for task in company_tasks:
                    if task.due_date == current_date + timedelta(days=1) and task.status != 'DONE':
                        notification = Notification.objects.filter(task=task.id)
                        if not notification:
                            Notification.objects.create(company=company, user=company.admin, task=task, message=f'{task.title} is due in one day')

                company_notifications = company.notifications.all()
                all_company_users = company.users.all()
                all_users = User.objects.exclude(id__in=all_company_users).exclude(id=company.admin.id)

                company_data = CompanySerializer(company).data
                company_data['tasks'] = TaskSerializer(company_tasks, many=True).data
                company_data['noncompanyusers'] = CustomUserSerializer(all_users, many=True).data
                company_data['notifications'] = NotificationSerializer(company_notifications, many=True).data
                company_data['admin_name'] = company.get_admin_email()

                all_companies_data.append(company_data)

            for personal in personal_accounts:
                if personal:
                    personal_tasks = personal.personal_tasks.all() or []
                    personal_data = {
                        "id": personal.id,
                        "name": personal.name,
                        "admin": CustomUserSerializer(personal.admin).data,
                        "tasks": TaskSerializer(personal_tasks, many=True).data
                    }
                    all_personal_accounts.append(personal_data)

            return Response({"companies": all_companies_data, "personals": all_personal_accounts}, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({'detail': 'No company or personal account found'}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
@api_view(['POST'])
def edit_profile(request, userid):
    if not userid:
        return Response({'detail': 'User ID is required'}, status=status.HTTP_401_UNAUTHORIZED)
    user = User.objects.get(id=userid)
    if request.method == "POST":
        email = request.data.get('email')
        username = request.data.get('username')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        profile_picture = request.FILES.get('profile_picture')
        password = request.data.get('password')

        if username:
            user.username = username

        if first_name:
            user.first_name = first_name

        if last_name:
            user.last_name = last_name

        if profile_picture:
            user.profile_picture = profile_picture
        
        if email:
            user.email = email

        if password:
            user.set_password(password)

        user.save()
        serialized = CustomUserSerializer(user).data
        return Response({'detail': 'Profile updated successfully', 'user': serialized}, status=200)
    else:
        return Response({'detail': 'Invalid request method'}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

@api_view(["POST", "DELETE"])
def create_personal_system(request, userid):
    if not userid:
            return Response({'detail': 'User ID is required'}, status=status.HTTP_400_BAD_REQUEST)
    if request.method == 'POST':
        if not request.data.get('name'):
            return Response({'detail': 'Account name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if Personal_Account.objects.filter(name=request.data.get('name')).exists():
            return Response({'detail': 'Personal account already exists'}, status=status.HTTP_409_CONFLICT)
        else:
            try:
                name = request.data.get('name')
                admin_id = request.data.get('admin')
                if admin_id:
                    admin = User.objects.get(id=admin_id)
                else:
                    admin = request.user
                personal_account = Personal_Account.objects.create(name=name, admin=admin)
                personal_account = Personal_AccountSerializer(personal_account).data
                return Response({'detail': 'Personal account created', 'personal': personal_account}, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    elif request.method == 'DELETE':
        try:
            personal_account = Personal_Account.objects.get(admin__id=userid)
            personal_account.delete()
            return Response({'detail': 'Personal account deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Personal_Account.DoesNotExist:
            return Response({'detail': 'Personal account not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def personal_task_view(request, personalid=None, taskid=None):
    if request.method == 'GET':
        if taskid: 
            try:
                task = Task.objects.prefetch_related('comments').get(id=taskid, personal__id=personalid)
                task_data = TaskSerializer(task).data
                return Response({'detail': 'Task fetched', 'task': task_data}, status=status.HTTP_200_OK)
            except Task.DoesNotExist:
                return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        else:  
            try:
                tasks = Task.objects.filter(personal__id=personalid)
                tasks_data = TaskSerializer(tasks, many=True).data
                return Response({'detail': 'Tasks fetched', 'tasks': tasks_data}, status=status.HTTP_200_OK)
            except Personal_Account.DoesNotExist:
                return Response({'detail': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        try:
            title = request.data.get('title')
            description = request.data.get('description')
            category_id = request.data.get('category') or None

            personal = Personal_Account.objects.get(id=personalid)
            due_date = request.data.get('due_date')
            if category_id:
                print(category_id)
                category = Category.objects.get(id=category_id)

                task = Task.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                personal=personal,
                category=category,
                due_date=due_date or default_due_date()
                )
            else:
                print('No category ID')
                task = Task.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                personal=personal,
                due_date=due_date or default_due_date()
                )
            
            task_data = TaskSerializer(task).data
            return Response({'detail': 'Task created', 'task': task_data}, status=status.HTTP_201_CREATED)
        except ObjectDoesNotExist:
            return Response({'detail': 'Company or User not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
            
    elif request.method == 'PUT':
        try:
            task_id = taskid
            task = Task.objects.get(id=task_id, personal__id=personalid)
            title = request.data.get('title')
            description = request.data.get('description')
            category_id = request.data.get('category')
            category = Category.objects.get(id=category_id) if category_id else None
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
            if category: 
                task.category = category
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
            task = Task.objects.get(id=task_id, personal__id=personalid)
            task.delete()
            return Response({'detail': 'Task deleted'}, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response({'detail': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
def category_view(request, personalid=None, categoryid=None):
    def get_category_data(category):
        return {
            'id': category.id,
            'name': category.name,
            'personal': category.personal.id if category.personal else None
        }

    if request.method == 'GET':
        if categoryid:
            try:
                category = Category.objects.get(id=categoryid)
                return Response({'detail': 'Category fetched', 'category': get_category_data(category)}, status=status.HTTP_200_OK)
            except Category.DoesNotExist:
                return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                personal = Personal_Account.objects.get(id=personalid)
                categories = Category.objects.filter(personal=personal)
                categories_data = [get_category_data(category) for category in categories]
                return Response({'detail': 'Categories fetched', 'categories': categories_data}, status=status.HTTP_200_OK)
            except Personal_Account.DoesNotExist:
                return Response({'detail': 'Personal account not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'POST':
        name = request.data.get('name')
        personal_id = request.data.get('personal')
        if not name:
            return Response({'detail': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            personal = Personal_Account.objects.get(id=personal_id) if personal_id else None
            category = Category.objects.create(name=name, personal=personal)
            return Response({'detail': 'Category created', 'category': get_category_data(category)}, status=status.HTTP_201_CREATED)
        except Personal_Account.DoesNotExist:
            return Response({'detail': 'Personal account not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'PUT':
        if not categoryid:
            return Response({'detail': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = Category.objects.get(id=categoryid)
            name = request.data.get('name')
            personal_id = request.data.get('personal')
            if name:
                category.name = name
            if personal_id:
                try:
                    personal = Personal_Account.objects.get(id=personal_id)
                    category.personal = personal
                except Personal_Account.DoesNotExist:
                    return Response({'detail': 'Personal account not found'}, status=status.HTTP_404_NOT_FOUND)
            category.save()
            return Response({'detail': 'Category updated', 'category': get_category_data(category)}, status=status.HTTP_200_OK)
        except Category.DoesNotExist:
            return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

    elif request.method == 'DELETE':
        if not categoryid:
            return Response({'detail': 'Category ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            category = Category.objects.get(id=categoryid)
            category.delete()
            return Response({'detail': 'Category deleted'}, status=status.HTTP_204_NO_CONTENT)
        except Category.DoesNotExist:
            return Response({'detail': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def get_users_for_admin(request):
    try:
        search_query = request.query_params.get('search', '')
        model = request.query_params.get('model')
        if model == 'company':
            users = User.objects.filter(company__isnull=True, is_superuser=False)
        elif model == 'personal':
            users = User.objects.filter(personal__isnull=True, is_superuser=False)
        else:
            users = User.objects.all()
        
        if search_query:
            users = users.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        

        serialized = CustomUserSerializer(users, many=True).data
        return Response(
            {
                'detail': 'Users fetched',
                'all_users': serialized,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        print(f"Error fetching users: {e}")
        return Response(
            {'detail': 'Error encountered', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    
@api_view(['GET', "DELETE"])
def all_unfiltered_users(request, userid=None):
    if request.method == 'GET':
        try:
            users = User.objects.exclude(id=request.user.id)
            serialized = CustomUserSerializer(users, many=True).data
            return Response(
                {
                    'detail': 'All users fetched',
                    'all_users': serialized,
                },
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'detail': 'Error encountered', 'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    if request.method == 'DELETE':
        try:
            user = get_object_or_404(User, id=userid)
            if request.user or request.user.is_superuser:
                user.delete()
                return Response({'detail': 'User deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
            else:
                return Response({'detail': 'You do not have permission to delete this user'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({'detail': 'Error encountered', 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
def home(request):
    return render(request, 'Home.html')