from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, get_user_model, authenticate, logout
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .serializer import CustomUserSerializer
from task_management.models import Company
from task_management.serializers import CompanySerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q
import logging

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([email, password]):
        return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    user = authenticate(request, email=email, password=password)
    if user is not None:
        login(request, user)
        refresh = RefreshToken.for_user(user)

        user_info = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': CustomUserSerializer(user).data,
        }
        # admin_companies = Company.objects.filter(admin=user)
        # user_companies = Company.objects.filter(companyuser__user=user) or None

        # if admin_companies.exists():
        #     all_companies = admin_companies
        #     user_info['companies'] = CompanySerializer(all_companies, many=True).data
        #     user_info['detail'] = 'Admin, User companies found'
        # elif user_companies.exists():
        #     all_companies = user_companies
        #     user_info['companies'] = CompanySerializer(all_companies, many=True).data
        #     user_info['detail'] = 'Employee, User companies found'
        # else:
        #     user_info['companies'] = []
        #     user_info['detail'] = 'No companies found for the user'

        return Response(user_info, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        logout(request)
        return Response({'detail': 'Successfully logged out!'}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    data = request.data
    email = data.get('email')
    username = data.get('username')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    password = data.get('password')
    password2 = data.get('password2')

    # if password != password2:
    #     return Response({'detail': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(email=data.get('email')).exists():
        return Response({'detail': 'Email is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=data.get('username')).exists():
        return Response({'detail': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            email=data.get('email'),
            password=data.get('password'),
            username=data.get('username'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
        )
        login(request, user, backend='custom_user_model.backends.CustomAuthBackend')
        refresh = RefreshToken.for_user(user)
        return Response({
            'detail': 'Registration successful!',
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': CustomUserSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'detail': ', '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_users(request):
    try:
        search_query = request.query_params.get('search', '')

        if search_query:
            users = User.objects.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        else:
            users = User.objects.all()

        serialized = CustomUserSerializer(users, many=True).data
        return Response(
            {
                'detail': 'Users fetched',
                'all_users': serialized,
            },
            status=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error fetching users: {e}")
        return Response(
            {'detail': 'Error encountered', 'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )