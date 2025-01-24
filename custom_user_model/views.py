from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth import login, get_user_model, authenticate, logout
from datetime import timedelta
from django.db.models import Q
from task_management.models import Company
from django.core.exceptions import ObjectDoesNotExist

User = get_user_model() 

@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    email = request.data.get('email')
    password = request.data.get('password')

    if not all([email, password]):
        return Response({'detail': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            user_info = {
                'refresh': str(refresh),
                'access': str(refresh.access_token)
            }

            all_companies = Company.objects.filter(Q(admin=user) | Q(companyuser__user=user))
            
            if all_companies.exists():
                user_info['companies'] = all_companies
                user_info['details'] = 'User companies found'
            else:
                user_info['details'] = 'No companies found for the user'
            
            return Response(user_info, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except User.DoesNotExist:
        return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    except ObjectDoesNotExist:
        return Response({'details': 'No object found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'details': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'detail': 'Successfully logged out!'}, status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'detail': f'error({e})'},status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    data = request.data
    if not all(data.get(field) for field in ('email', 'username', 'first_name', 'last_name', 'password', 'password2')):
        return Response({'detail': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

    if data.get('password') != data.get('password2'):
        return Response({'detail': 'Passwords do not match.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        User.objects.get(email=data.get('email'))
        return Response({'detail': 'Email is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'detail': ', '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        pass

    try:
        User.objects.get(username=data.get('username'))
        return Response({'detail': 'Username is already taken.'}, status=status.HTTP_400_BAD_REQUEST)
    except ValidationError as e:
        return Response({'detail': ', '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)
    except User.DoesNotExist:
        pass

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
        return Response({'detail':'Registration successful!', 'refresh': str(refresh), 'access': str(refresh.access_token)}, status=status.HTTP_201_CREATED)
    except ValidationError as e:
        return Response({'detail': ', '.join(e.messages)}, status=status.HTTP_400_BAD_REQUEST)