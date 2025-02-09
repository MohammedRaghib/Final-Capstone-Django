from django.urls import path
from . import views

urlpatterns = [
    # Home Page
    path('', views.home, name='home'),

    # Category
    path('categories/', views.category_view, name='category_list_create'),  # Category GET, POST
    path('categories/<int:categoryid>/', views.category_view, name='category_detail_update_delete'),  # Category PUT, DELETE

    # Personal
    path('create-personal/<int:userid>/', views.create_personal_system, name='create_personal_system'), # If creating a personal system then updates user profile

    path('personal/<int:personalid>/tasks/', views.personal_task_view, name='personal_task_list_create'),  # Personal Task GET, POST 
    path('personal/<int:personalid>/tasks/<int:taskid>/', views.personal_task_view, name='personal_task_detail_update_delete'),  # Personal Task PUT, DELETE

    # Company
    path('companies/', views.company_view, name='company_list_create'),  # Company GET, POST
    path('companies/<int:companyid>/', views.company_view, name='company_detail_update_delete'),  # Company PUT, DELETE

    # CompanyUser
    path('company/<int:companyid>/users/', views.company_user_view, name='company-users'),  # CompanyUser GET, POST 
    path('company/<int:companyid>/users/<int:userid>/', views.company_user_view, name='company-user-delete'),  # CompanyUser DELETE

    # Specific User
    path('usercompanies/', views.get_user_companies, name='get_user_companies'),  # Getting company for request.user
    path('tasks/assignedto/<int:userid>/', views.get_tasks_assigned_to_user, name='tasks-assigned-to-user'), # Getting tasks assigned to user
    path('accept_or_decline_invite/<int:userid>/<int:companyid>/', views.Accept_or_decline_invite, name='accept_or_decline_invite'), # Accept or declining invite
    path('edit_profile/<int:userid>/', views.edit_profile, name='edit_profile'), # Editing user profile
    path('create-personal/<int:userid>/', views.create_personal_system, name='create_personal_system'), # If creating a personal system then updates user profile

    # Tasks
    path('companies/<int:companyid>/tasks/', views.task_view, name='task_list_create'),  # Task GET, POST 
    path('companies/<int:companyid>/tasks/<int:taskid>/', views.task_view, name='task_detail_update_delete'),  # Task PUT, DELETE

    # Comment
    path('tasks/<int:taskid>/comments/', views.comment_view, name='comment_list_create'),  # Comment GET, POST 
    path('tasks/<int:taskid>/comments/<int:commentid>/', views.comment_view, name='comment_detail_delete'),  # Comment PUT, DELETE

    # Admin
    path('overalladmin/allcompanies/', views.fetch_data, name='fetch_data'), # Get all company objects for overall admin
    path('getusersforadmin/', views.get_users_for_admin, name='get_users_for_admin'), # Get all filtered user objects for overall admin
    path('allunfilteredusers/', views.all_unfiltered_users, name='all_unfiltered_users_get'), # Get all unfiltered user objects for overall admin
    path('allunfilteredusers/<int:userid>/', views.all_unfiltered_users, name='all_unfiltered_users_delete'), # Delete unfiltered user object for overall admin

    # Notification
    path('notifications/<int:userid>/', views.notification_view, name='notification_list_create'),  # Notification GET, POST 
    path('notifications/<int:userid>/<int:notificationid>/', views.notification_view, name='notification_detail_delete'),  #Notification PUT, DELETE
]
