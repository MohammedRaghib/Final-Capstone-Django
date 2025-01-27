from django.urls import path
from . import views

urlpatterns = [
    path('companies/', views.company_view, name='company_list_create'),  # Company GET, POST
    path('companies/<int:companyid>/', views.company_view, name='company_detail_update_delete'),  # Company PUT, DELETE

    path('usercompanies/', views.get_user_companies, name='get_user_companies'),  # Getting company for request.user

    path('companies/<int:companyid>/tasks/', views.task_view, name='task_list_create'),  # Task GET, POST 
    path('companies/<int:companyid>/tasks/<int:taskid>/', views.task_view, name='task_detail_update_delete'),  # Task PUT, DELETE

    path('companies/<int:companyid>/users/', views.company_user_view, name='company_user_list_create'),  # CompanyUser GET, POST 

    path('tasks/<int:taskid>/comments/', views.comment_view, name='comment_list_create'),  # Comment GET, POST 
    path('tasks/<int:taskid>/comments/<int:commentid>/', views.comment_view, name='comment_detail_delete'),  # Comment PUT, DELETE

    path('notifications/<int:userid>/', views.notification_view, name='notification_list_create'),  # Notification GET, POST 
    path('notifications/<int:userid>/<int:notificationid>/', views.notification_view, name='notification_detail_delete'),  #Notification PUT, DELETE
]
